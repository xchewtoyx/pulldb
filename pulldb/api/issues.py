from datetime import date
from functools import partial
import json
import logging

from google.appengine.api import search
from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models.issues import Issue, issue_key, issue_context
from pulldb.models.issues import refresh_issue_shard
from pulldb.models.subscriptions import Subscription
from pulldb.models import comicvine
from pulldb.models import volumes
from pulldb.models.volumes import Volume

@ndb.tasklet
def refresh_issue_volume(volume):
    comicvine_volume = comicvine.Volume(volume.identifier)
    comicvine_issues = list(comicvine_volume.issues)
    issues = []
    for index in range(0, len(comicvine_issues), 100):
        ids = '|'.join(
            [str(issue.id) for issue in comicvine_issues[
                index:max([len(comicvine_issues), index+100])]])
        issue_page = comicvine.Issues(
            filter="id:%s" % ids, field_list=[
                'id', 'store_date', 'image', 'issue_number', 'name',
                'site_detail_url', 'cover_date'])
        for issue in issue_page:
            issues.append(issue_key(
                issue, volume_key=volume.key, create=True, reindex=True))
    raise ndb.Return(issues)

class GetIssue(OauthHandler):
    def get(self, identifier):
        query = Issue.query(Issue.identifier==int(identifier))
        results = query.fetch()
        self.response.write(JsonModel().encode(list(results)))

class RefreshShard(OauthHandler):
    def get(self, shard_count=None, shard=None):
        if not shard_count:
            # When run from cron cycle over all issues
            shard_count=24 * 7
            shard=datetime.today().hour + 24 * date.today().weekday()
        comicvine.load()
        refresh_callback = partial(
            refresh_issue_shard, int(shard), int(shard_count))
        query = Subscription.query(projection=('volume',), distinct=True)
        volume_keys = query.map(refresh_callback)
        volume_count = sum([1 for volume in volume_keys if volume])
        issue_count = sum([len(volume) for volume in volume_keys if volume])
        status = 'Updated %d issues in %d/%d volumes' % (
            issue_count, update_count, len(volume_keys))
        logging.info(status)
        self.response.write(json.dumps({
            'status': 200,
            'message': status,
        }))

class RefreshVolume(OauthHandler):
    def get(self, volume):
        comicvine.load()
        refresh_callback = partial(refresh_issue_volume)
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

class SearchIssues(OauthHandler):
    def get(self):
        index = search.Index(name='issues')
        issues = index.search(self.request.get('q'))
        logging.debug('results: %r', issues)
        issue_keys = [
            ndb.Key(urlsafe=issue.doc_id) for issue in issues.results]
        query = Issue.query(Issue.key.IN(issue_keys))
        results = query.map(issue_context)
        self.response.write(JsonModel().encode(list(results)))

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
])
