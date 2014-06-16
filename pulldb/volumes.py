# Copyright 2013 Russell Heilling

from datetime import datetime
import logging
from math import ceil
import re

from google.appengine.api import search
from google.appengine.ext import ndb

import pycomicvine

from pulldb import base
from pulldb import publishers
from pulldb import subscriptions
from pulldb import users
from pulldb import util
from pulldb.api.volumes import RefreshVolumes
from pulldb.models.admin import Setting
from pulldb.models.volumes import Volume, volume_key

class MainPage(base.BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template = self.templates.get_template('volumes.html')
    self.response.write(template.render(template_values))

class Search(base.BaseHandler):
  def get(self):
    def volume_detail(comicvine_volume):
      try:
        volume = volume_key(comicvine_volume).get()
        subscription = False
        subscription_key = subscriptions.subscription_key(volume.key)
        if subscription_key:
          subscription = subscription_key.urlsafe()
        publisher_key = volume.publisher
        publisher = None
        if publisher_key:
          publisher = publisher_key.get()
        return {
          'volume_key': volume.key.urlsafe(),
          'volume': volume,
          'publisher': publisher,
          'subscribed': bool(subscription),
        }
      except AttributeError:
        logging.warn('Could not look up volume %r', comicvine_volume)

    # TODO(rgh): This should probably be initialised somewhere else
    pycomicvine.api_key = Setting.query(
      Setting.name == 'comicvine_api_key').get().value
    query = self.request.get('q')
    volume_ids = self.request.get('volume_ids')
    page = int(self.request.get('page', 0))
    limit = int(self.request.get('limit', 20))
    offset = page * limit
    if volume_ids:
      volumes = re.findall(r'(\d+)', volume_ids)
      logging.debug('Found volume ids: %r', volumes)
      volume_filter = '|'.join(volumes)
      logging.debug('filter=id:%s', volume_filter)
      results = pycomicvine.Volumes(
        filter="id:%s" % (volume_filter,), field_list=[
          'id', 'name', 'start_year', 'count_of_issues',
          'deck', 'image', 'site_detail_url', 'publisher',
          'date_last_updated'])
      logging.debug('Found volumes: %r' % results)
    elif query:
      results = pycomicvine.Volumes.search(
        query=query, field_list=[
          'id', 'name', 'start_year', 'count_of_issues',
          'deck', 'image', 'site_detail_url', 'publisher',
          'date_last_updated'])
      logging.debug('Found volumes: %r' % results)
    if offset + limit > len(results):
      page_end = len(results)
    else:
      page_end = offset + limit
    logging.info('Retrieving results %d-%d / %d', offset, page_end,
                 len(results))
    results_page = results[offset:page_end]
    template_values = self.base_template_values()

    template_values.update({
      'query': query,
      'volume_ids': volume_ids,
      'page': page,
      'limit': limit,
      'results': (volume_detail(volume) for volume in results_page),
      'results_count': len(results),
      'page_url': util.StripParam(self.request.url, 'page'),
      'page_count': int(ceil(1.0*len(results)/limit)),
    })
    template = self.templates.get_template('volumes_search.html')
    self.response.write(template.render(template_values))

app = base.create_app([
  ('/volumes', MainPage),
  ('/volumes/search', Search),
  ('/tasks/volumes/refresh', RefreshVolumes),
])
