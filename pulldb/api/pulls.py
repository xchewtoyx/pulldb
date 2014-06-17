import json
import logging

from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models.issues import Issue, issue_key, issue_context
from pulldb.models.issues import refresh_issue_shard, refresh_issue_volume
from pulldb.models.pulls import Pull
from pulldb.models.subscriptions import Subscription
from pulldb.models import volumes
from pulldb.models.volumes import Volume

@ndb.tasklet
def issue_pull_context(issue):
    pull = yield Pull.query(Pulls.issue==issue).get_async()
    raise ndb.Return({
        'pull': pull.get().to_dict(),
        'issue': issue.to_dict(),
    })

@ndb.tasklet
def pull_context(pull):
    issue = yield ndb.Key(pull.issue).get_async()
    raise ndb.Return({
        'pull': pull.to_dict(),
        'issue': issue.to_dict(),
    })

class GetPull(OauthHandler):
    def get(self, identifier):
        query = Issue.query(Issue.identifier==int(identifier))
        result = query.map(issue_pull_context)
        self.response.write({
            'status': 200,
            'pull': result['pull'],
            'issue': result['issue'],
        })

class ListPulls(OauthHandler):
    def get(self):
        user_key = users.user_key(self.user)
        query = Pull.query(ancestor=user_key)
        results = query.map(pull_context)
        pulls = []
        for result in results:
            pulls.append({
                'pull': result['pull'],
                'issue': result['issue'],
            })
        self.response.write(json.dumps({
            'status': 200,
            'results': results,
        }))

app = create_app([
    Route(
        '/api/pulls/get/<identifier>',
        'pulldb.api.pulls.GetPull',
    ),
    Route(
        '/api/pulls/list',
        'pulldb.api.pulls.ListPulls',
    ),
])
