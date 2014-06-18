from datetime import datetime, date
from functools import partial
import json
import logging

from google.appengine.api import search
from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, TaskHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models.admin import Setting
from pulldb.models.issues import Issue, issue_key, issue_context
from pulldb.models.issues import refresh_issue_shard, refresh_issue_volume
from pulldb.models.subscriptions import Subscription
from pulldb.models import comicvine
from pulldb.models import volumes
from pulldb.models.volumes import Volume

class GetIssue(OauthHandler):
    def get(self, identifier):
        query = Issue.query(Issue.identifier==int(identifier))
        results = query.fetch()
        self.response.write(JsonModel().encode(list(results)))

class RefreshShard(TaskHandler):
    def get(self, shard_count=None, shard=None):
        if not shard_count:
            # When run from cron cycle over all issues
            shard_count=24 * 7
            shard=datetime.today().hour + 24 * date.today().weekday()
        cv = comicvine.load()
        query = Issue.query(Issue.shard==int(shard))
        comicvine_issues = [issue.identifier for issue in query.fetch()]
        issues = []
        for index in range(0, len(comicvine_issues), 100):
            ids = [str(issue) for issue in comicvine_issues[
                index:min([len(comicvine_issues), index+100])]]
            issue_page = cv.fetch_issue_batch(ids)
            for issue in issue_page:
                issues.append(issue_key(issue, create=False, reindex=True))
        status = 'Updated %d issues' % len(issues)
        logging.info(status)
        self.response.write(json.dumps({
            'status': 200,
            'message': status,
        }))

class RefreshVolume(OauthHandler):
    def get(self, volume):
        cv = comicvine.load()
        refresh_callback = partial(refresh_issue_volume, comicvine=cv)
        query = Volume.query(Volume.identifier == int(volume))
        volume_keys = query.map(refresh_callback)
        volume_count = sum([1 for volume in volume_keys if volume])
        issue_count = sum([len(volume) for volume in volume_keys if volume])
        status = 'Updated %d issues in %d/%d volumes' % (
            issue_count, volume_count, len(volume_keys))
        logging.info(status)
        self.response.write(json.dumps({
            'status': 200,
            'message': status,
        }))


class ReshardIssues(TaskHandler):
    @ndb.tasklet
    def reshard_task(self, shards, issue):
        issue.shard = issue.identifier % shards
        result = yield issue.put_async()
        raise ndb.Return(result)

    def get(self):
        shards_key = Setting.query(Setting.name == 'update_shards_key').get()
        shards = int(shards_key.value)
        callback = partial(self.reshard_task, shards)
        query = Issue.query()
        results = query.map(callback)
        self.response.write(json.dumps({
            'status': 200,
            'message': '%d issues resharded' % len(results),
        }))

class SearchIssues(OauthHandler):
    def get(self):
        index = search.Index(name='issues')
        results = []
        issues = index.search(self.request.get('q'))
        logging.debug('results: %r', issues)
        for issue in issues:
            result = {
                'id': issue.doc_id,
                'rank': issue.rank,
            }
            for field in issue.fields:
                result[field.name] = str(field.value)
            results.append(result)
        self.response.write(json.dumps({
            'status': 200,
            'count': issues.number_found,
            'results': results,
        }))

class Validate(TaskHandler):
    @ndb.tasklet
    def check_valid(self, issue):
        if issue.key.id() != str(issue.identifier):
            deleted = yield issue.key.delete_async()
            raise ndb.Return(True)

    def get(self):
        query = Issue.query()
        results = query.map(self.check_valid)
        deleted = sum(1 for deleted in results if deleted)
        self.response.write(json.dumps({
            'status': 200,
            'deleted': deleted,
        }))

app = create_app([
    Route(
        '/api/issues/get/<identifier>',
        'pulldb.api.issues.GetIssue'
    ),
    Route(
        '/api/issues/refresh/<shard_count>/<shard>',
        'pulldb.api.issues.RefreshShard'
    ),
    Route(
        '/api/issues/refresh/<volume>',
        'pulldb.api.issues.RefreshVolume'
    ),
    Route(
        '/api/issues/search',
        'pulldb.api.issues.SearchIssues'
    ),
    Route(
        '/tasks/issues/refresh',
        'pulldb.api.issues.RefreshShard'
    ),
    Route(
        '/tasks/issues/reshard',
        'pulldb.api.issues.ReshardIssues'
    ),
    Route(
        '/tasks/issues/validate',
        'pulldb.api.issues.Validate'
    ),
])
