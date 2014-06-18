from datetime import date, datetime
from functools import partial
import json
import logging

from google.appengine.api import search
from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, TaskHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models.admin import Setting
from pulldb.models import comicvine
from pulldb.models.issues import Issue
from pulldb.models.subscriptions import Subscription
from pulldb.models import volumes
from pulldb.models.volumes import Volume, volume_context
from pulldb.models.volumes import refresh_volume_shard

class GetVolume(OauthHandler):
    def get(self, identifier):
        volume_key = ndb.Key(Volume, identifier)
        volume = volume_key.get()
        if volume:
            publisher = volume.publisher.get()
            volume_dict = volume.to_dict()
            publisher_dict = publisher.to_dict()
            response = {
                'status': 200,
                'message': 'matching volume found',
                'volume': {
                    key: unicode(value) for key, value in volume_dict.items()
                },
                'publisher': {
                    key: unicode(value) for key, value in publisher_dict.items()
                }
            }
        else:
            response = {
                'status': 404,
                'message': 'no matching volume found',
            }
        self.response.write(json.dumps(response))

class RefreshVolumes(TaskHandler):
    @ndb.tasklet
    def volume_issues(self, volume):
        issues = yield Issue.query(ancestor=volume.key).fetch_async()
        issue_ids = [issue.identifier for issue in issues]
        raise ndb.Return({
            'volume': volume.identifier,
            'volume_key': volume.key,
            'ds_issues': issue_ids,
        })

    def get(self, shard_count=None, shard=None):
        if not shard_count:
            # When run from cron cycle over all issues weekly
            shard_count=24 * 7
            shard=datetime.today().hour + 24 * date.today().weekday()
        cv = comicvine.load()
        query = Volume.query(Volume.shard==int(shard))
        results = query.map(self.volume_issues)
        sharded_ids = [result['volume'] for result in results]
        volume_detail = {}
        for result in results:
            volume_detail[result['volume']] = result
        cv_volumes = []
        for index in range(0, len(sharded_ids), 100):
            volume_page = sharded_ids[index:min(index+100, len(sharded_ids))]
            cv_volumes.extend(cv.fetch_volume_batch(volume_page))
        for comicvine_volume in cv_volumes:
            logging.debug('checking for new issues in %r', comicvine_volume)
            comicvine_id = comicvine_volume['id']
            comicvine_issues = comicvine_volume.get('issues', [])
            volume_detail[int(comicvine_id)]['cv_issues'] = comicvine_issues
            volumes.volume_key(comicvine_volume, create=False, reindex=True)
        new_issues = []
        for volume, detail in volume_detail.items():
            for issue in detail['cv_issues']:
                if int(issue['id']) not in detail['ds_issues']:
                    new_issues.append((issue, detail['volume_key']))
        for issue, volume_key in new_issues:
            issue_key(issue, volume_key=volume_key)
        status = 'Updated %d volumes. Found %d new issues' % (
            len(sharded_ids), len(new_issues)
        )
        logging.info(status)
        self.response.write(json.dumps({
            'status': 200,
            'message': status,
        }))

class ReshardVolumes(TaskHandler):
    @ndb.tasklet
    def reshard_task(self, shards, volume):
        volume.shard = volume.identifier % shards
        result = yield volume.put_async()
        raise ndb.Return(result)

    def get(self):
        shards_key = Setting.query(Setting.name == 'update_shards_key').get()
        shards = int(shards_key.value)
        callback = partial(self.reshard_task, shards)
        query = Volume.query()
        results = query.map(callback)
        self.response.write(json.dumps({
            'status': 200,
            'message': '%d volumes resharded' % len(results),
        }))

class SearchVolumes(OauthHandler):
    def get(self):
        index = search.Index(name='volumes')
        results = []
        try:
            volumes = index.search(self.request.get('q'))
            logging.debug('results: found %d matches', volumes.number_found)
            for volume in volumes.results:
                result = {
                    'id': volume.doc_id,
                    'rank': volume.rank,
                }
                for field in volume.fields:
                    result[field.name] = unicode(field.value)
                results.append(result)
        except search.Error as e:
            logging.exception(e)
        self.response.write(json.dumps({
            'status': 200,
            'count': volumes.number_found,
            'results': results,
        }))

class Validate(TaskHandler):
    @ndb.tasklet
    def drop_invalid(self, volume):
        if volume.key.id() != str(volume.identifier):
            deleted = yield volume.key.delete_async()
            raise ndb.Return(True)

    def get(self):
        query = Volume.query()
        results = query.map(self.drop_invalid)
        deleted = sum(1 for deleted in results if deleted)
        self.response.write(json.dumps({
            'status': 200,
            'deleted': deleted,
        }))

app = create_app([
    Route(
        '/api/volumes/get/<identifier>',
        'pulldb.api.volumes.GetVolume'
    ),
    Route(
        '/api/volumes/refresh/<shard_count>/<shard>',
        'pulldb.api.volumes.RefreshVolumes'
    ),
    Route(
        '/api/volumes/search',
        'pulldb.api.volumes.SearchVolumes'
    ),
    Route(
        '/tasks/volumes/refresh',
        'pulldb.api.volumes.RefreshVolumes'
    ),
    Route(
        '/tasks/volumes/validate',
        'pulldb.api.volumes.Validate'
    ),
])
