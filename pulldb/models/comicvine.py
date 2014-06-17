from functools import partial
import json
import logging
from urllib import urlencode

from google.appengine.api import memcache
from google.appengine.api import urlfetch

import pycomicvine
from pycomicvine import Issue, Issues, Volume
from pycomicvine import error
from pulldb.models.admin import Setting

class Comicvine(object):
    def __init__(self):
        self.api_base = 'https://www.comicvine.com/api'
        self.api_key = Setting.query(
            Setting.name == 'comicvine_api_key').get().value
        self.types = self._fetch_types()

    def __getattr__(self, attribute):
        if attribute.startswith('fetch_'):
            tokens = attribute.split('_')
            if len(tokens) > 2 and tokens[2] == 'batch':
                method = self._fetch_batch
            else:
                method = self._fetch_single
            resource = tokens[1]
            return partial(method, resource)

    def _fetch_url(self, path, **kwargs):
        query = {
            'api_key': self.api_key,
            'format': 'json',
        }
        query.update(**kwargs)
        query_string = urlencode(query)
        resource_url = '%s/%s?%s' % (
            self.api_base, path, query_string)
        logging.debug('Fetching comicvine resource: %s', resource_url)
        response = urlfetch.fetch(resource_url)
        logging.debug('Got response: %r' % response)
        try:
            reply = json.loads(response.content)
        except ValueError as e:
            logging.exception(e)
        else:
            if reply['error'] == 'OK':
                logging.debug('Success: %r', reply)
                return reply['results']
            logging.error('Error: %r', reply)

    def _fetch_types(self):
        types = memcache.get('types', namespace='comicvine')
        if types:
            types = json.loads(types)
        else:
            types = self._fetch_url('types')
            if types:
                type_dict = {}
                for resource_type in types:
                    resource_name = resource_type['detail_resource_name']
                    type_dict[resource_name] = resource_type
                types = type_dict
                # Types don't change often. cache for a week
                memcache.set('types', json.dumps(types), 604800,
                             namespace='comicvine')
        return types

    def _fetch_single(self, resource, identifier):
        resource_path = self.types[resource]['detail_resource_name']
        resource_type = self.types[resource]['id']
        path = '%s/%s-%d' % (resource_path, resource_type, identifier)
        return self._fetch_url(path)

    def _fetch_batch(self, resource, identifiers):
        path = self.types[resource]['list_resource_name']
        filter_string = 'id:%s' % '|'.join(str(id) for id in identifiers)
        return self._fetch_url(path, filter=filter_string)

def load():
    pycomicvine.api_key = Setting.query(
      Setting.name == 'comicvine_api_key').get().value
