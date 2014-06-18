from collections import defaultdict
from functools import partial
import json
import logging

from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models import issues
from pulldb.models import pulls
from pulldb.models import subscriptions
from pulldb.models import volumes
from pulldb.models.volumes import Volume

def model_to_dict(model):
    return { key: unicode(value) for key, value in model.to_dict().items() }

@ndb.tasklet
def issue_pull_context(issue):
    pull = yield pulls.Pull.query(pulls.Pulls.issue==issue).get_async()
    raise ndb.Return({
        'pull': model_to_dict(pull),
        'issue': model_to_dict(issue),
    })

@ndb.tasklet
def pull_context(pull):
    issue = yield pull.issue.get_async()
    volume = yield issue.key.parent().get_async()
    raise ndb.Return({
        'pull': model_to_dict(pull),
        'issue': model_to_dict(issue),
        'volume': model_to_dict(volume),
    })

class AddPulls(OauthHandler):
    def post(self):
        user_key = users.user_key(self.user)
        request = json.loads(self.request.body)
        issue_ids = request['issues']
        results = defaultdict(list)
        query = issues.Issue.query(issues.Issue.identifier.IN(
            [int(id) for id in issue_ids]))
        records = query.fetch()
        issue_dict = {record.key.id(): record for record in records}
        candidates = []
        for issue_id in issue_ids:
            issue = issue_dict.get(issue_id)
            if issue:
                pull_key = ndb.Key(
                    users.User, user_key.id(),
                    subscriptions.Subscription, issue.key.parent().id(),
                    pulls.Pull, issue_id,
                )
                candidates.append((issue.key, pull_key))
            else:
                logging.info('Unable to add pull, issue %s not found' % (
                    issue_id))
                results['failed'].append(issue_key.id())
        # prefetch for efficiency
        ndb.get_multi(pull for issue, pull in candidates)
        new_pulls = []
        for issue_key, pull_key in candidates:
            if pull_key.get():
                logging.info('Unable to add pull, issue %s already pulled' % (
                    issue_key.id()))
                # already exists
                results['failed'].append(pull_key.id())
            else:
                new_pulls.append(pulls.Pull(
                    key = pull_key,
                    issue = issue_key,
                    read = False,
                ))
                results['added'].append(pull_key.id())
        ndb.put_multi(new_pulls)
        response = {
            'status': 200,
            'results': results
        }
        self.response.write(json.dumps(response))

class GetPull(OauthHandler):
    def get(self, identifier):
        query = issues.Issue.query(issues.Issue.identifier==int(identifier))
        result = query.map(issue_pull_context)
        self.response.write({
            'status': 200,
            'pull': result['pull'],
            'issue': result['issue'],
        })

class ListPulls(OauthHandler):
    def get(self):
        user_key = users.user_key(self.user)
        query = pulls.Pull.query(ancestor=user_key)
        results = query.map(pull_context)
        self.response.write(json.dumps({
            'status': 200,
            'results': results,
        }))

class NewIssues(OauthHandler):
    @ndb.tasklet
    def check_pulled(self, subscription, issue):
        pull_key = ndb.Key(pulls.Pull, issue.key.id(), parent=subscription.key)
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

    def get(self):
        user_key = users.user_key(self.user)
        query = subscriptions.Subscription.query(ancestor=user_key)
        subs = [sub for sub in query.map(self.find_new_issues) if sub]
        new_issues = []
        for subscription, unread in subs:
            volume = subscription.volume.get()
            volume_dict = model_to_dict(volume)
            for issue in unread:
                new_issues.append({
                    'volume': volume_dict,
                    'issue': model_to_dict(issue),
                })
        result = {
            'status': 200,
            'results': new_issues,
        }
        self.response.write(json.dumps(result))

class UpdatePulls(OauthHandler):
    def post(self):
        user_key = users.user_key(self.user)
        request = json.loads(self.request.body)
        issue_ids = request.get('read', []) + request.get('unread', [])
        results = defaultdict(list)
        query = issues.Issue.query(issues.Issue.identifier.IN(
            [int(id) for id in issue_ids]))
        records = query.fetch()
        issue_dict = {record.key.id(): record for record in records}
        candidates = []
        for issue_id in issue_ids:
            issue = issue_dict.get(issue_id)
            if issue:
                pull_key = ndb.Key(
                    users.User, user_key.id(),
                    subscriptions.Subscription, issue.key.parent().id(),
                    pulls.Pull, issue.key.id(),
                )
                candidates.append(pull_key)
            else:
                # no such issue
                results['failed'].append(issue_key.id())
        # prefetch for efficiency
        ndb.get_multi(candidates)
        updated_pulls = []
        for pull_key in candidates:
            pull = pull_key.get()
            if pull:
                if pull.issue.id() in request.get('read', []):
                    if pull.read:
                        results['skipped'].append(pull_key.id())
                    else:
                        results['updated'].append(pull_key.id())
                        pull.read = True
                        updated_pulls.append(pull)
                if pull.issue.id() in request.get('unread', []):
                    if pull.read:
                        results['updated'].append(pull_key.id())
                        pull.read = False
                        updated_pulls.append(pull)
                    else:
                        results['skipped'].append(pull_key.id())
            else:
                # No such pull
                results['failed'].append(pull_key.id())
        ndb.put_multi(updated_pulls)
        response = {
            'status': 200,
            'results': results
        }
        self.response.write(json.dumps(response))

app = create_app([
    Route(
        '/api/pulls/add',
        'pulldb.api.pulls.AddPulls',
    ),
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
    Route(
        '/api/pulls/update',
        'pulldb.api.pulls.UpdatePulls',
    ),
])
