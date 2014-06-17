from datetime import date
from functools import partial
import json
import logging

from google.appengine.api import search
from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, TaskHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models import comicvine
from pulldb.models.subscriptions import Subscription
from pulldb.models.volumes import Volume, volume_context, volume_key
from pulldb.models.volumes import refresh_volume_shard

class GetVolume(OauthHandler):
    def get(self, identifier):
        query = Volume.query(Volume.identifier==int(identifier))
        results = query.map(volume_context)
        self.response.write(JsonModel().encode(list(results)))

class RefreshVolumes(TaskHandler):
    def get(self, shard_count=None, shard=None):
        if not shard_count:
            # When run from cron cycle over all issues weekly
            shard_count=7
            shard=date.today().weekday()
        cv = comicvine.load()
        refresh_callback = partial(
            refresh_volume_shard, int(shard), int(shard_count), comicvine=cv)
        query = Subscription.query(projection=('volume',), distinct=True)
        volume_ids = query.map(refresh_callback)
        sharded_ids = [id for id in volume_ids if id]
        volumes = []
        for index in range(0, len(sharded_ids), 100):
            volume_page = sharded_ids[index:min(index+100, len(sharded_ids))]
            volumes.extend(cv.fetch_volume_batch(volume_page))
        for comicvine_volume in volumes:
            volume_key(comicvine_volume, create=False, reindex=True)
        status = 'Updated %d/%d volumes' % (
            len(sharded_ids), len(volume_ids))
        logging.info(status)
        self.response.write(json.dumps({
            'status': 200,
            'message': status,
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
])
