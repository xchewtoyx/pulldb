from datetime import date
from functools import partial
import json
import logging

from google.appengine.api import search
from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models.volumes import Volume, volume_context, volume_key
from pulldb.models.subscriptions import Subscription
from pulldb.models import comicvine

@ndb.tasklet
def refresh_volume_shard(shard, shard_count, subscription):
    volume = yield subscription.volume.get_async()
    if volume.identifier % shard_count == shard:
        comicvine_volume = comicvine.Volume(volume.identifier)
        updated_key = volume_key(comicvine_volume, create=False, reindex=True)
        raise ndb.Return(updated_key)

class GetVolume(OauthHandler):
    def get(self, identifier):
        query = Volume.query(Volume.identifier==int(identifier))
        results = query.map(volume_context)
        self.response.write(JsonModel().encode(list(results)))

class RefreshVolumes(OauthHandler):
    def get(self, shard_count=None, shard=None):
        if not shard_count:
            # When run from cron cycle over all issues weekly
            shard_count=7
            shard=date.today().weekday()
        comicvine.load()
        refresh_callback = partial(
            refresh_volume_shard, int(shard), int(shard_count))
        query = Subscription.query(projection=('volume',), distinct=True)
        volume_keys = query.map(refresh_callback)
        update_count = sum([1 for volume in volume_keys if volume])
        status = 'Updated %d/%d volumes' % (
            update_count, len(volume_keys))
        logging.info(status)
        self.response.write(json.dumps({
            'status': 200,
            'message': status,
        }))

class SearchVolumes(OauthHandler):
    def get(self):
        index = search.Index(name='volumes')
        volumes = index.search(self.request.get('q'))
        logging.debug('results: %r', volumes)
        volume_keys = [
            ndb.Key(urlsafe=volume.doc_id) for volume in volumes.results]
        results = ndb.get_multi(volume_keys)
        self.response.write(JsonModel().encode(list(results)))

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
])
