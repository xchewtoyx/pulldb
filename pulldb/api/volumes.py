import json
import logging

from google.appengine.api import search
from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models.volumes import Volume, volume_context

class GetVolume(OauthHandler):
    def get(self, identifier):
        query = Volume.query(Volume.identifier==int(identifier))
        results = query.map(volume_context)
        self.response.write(JsonModel().encode(list(results)))

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
        '/api/volumes/search',
        'pulldb.api.volumes.SearchVolumes'
    ),
])
