from functools import partial
import json
import logging

from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models import issues
from pulldb.models.pulls import Pull
from pulldb.models import subscriptions
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

class NewIssues(OauthHandler):
    @ndb.tasklet
    def check_pulled(self, subscription, issue):
        pull_key = ndb.Key(Pull, issue.key.id(), parent=subscription.key)
        pull = yield pull_key.get_async()
        if not pull:
            raise ndb.Return(issue)

    @ndb.tasklet
    def find_new_issues(self, subscription):
        pull_check_callback = partial(self.check_pulled, subscription)
        query = issues.Issue.query(
            ancestor=subscription.volume).filter(
                issues.Issue.pubdate > subscription.start_date).order(
                    issues.Issue.pubdate)
        volume, results = yield (
            subscription.volume.get_async(),
            query.map_async(pull_check_callback))
        if results:
            raise ndb.Return(
                subscription,
                [issue for issue in results if issue]
            )

    def model_to_dict(self, model):
        return {
            key: unicode(value) for key, value in model.to_dict().items()
        }

    def get(self):
        user_key = users.user_key(self.user)
        query = subscriptions.Subscription.query(ancestor=user_key)
        subs = [sub for sub in query.map(self.find_new_issues) if sub]
        new_issues = []
        for subscription, unread in subs:
            volume = subscription.volume.get()
            volume_dict = self.model_to_dict(volume)
            for issue in unread:
                new_issues.append({
                    'volume': volume_dict,
                    'issue': self.model_to_dict(issue),
                })
        result = {
            'status': 200,
            'results': new_issues,
        }
        self.response.write(json.dumps(result))

app = create_app([
    Route(
        '/api/pulls/get/<identifier>',
        'pulldb.api.pulls.GetPull',
    ),
    Route(
        '/api/pulls/list',
        'pulldb.api.pulls.ListPulls',
    ),
    Route(
        '/api/pulls/new',
        'pulldb.api.pulls.NewIssues',
    ),
])
