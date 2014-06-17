# Copyright 2013 Russell Heilling

from datetime import datetime, date
import logging
from math import ceil
import re

from google.appengine.api import search
from google.appengine.ext import ndb

import pycomicvine

from pulldb import base
from pulldb import publishers
from pulldb import subscriptions
from pulldb import util
from pulldb.models.admin import Setting
from pulldb.models import comicvine
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

    cv = comicvine.load()
    query = self.request.get('q')
    volume_ids = self.request.get('volume_ids')
    page = int(self.request.get('page', 0))
    limit = int(self.request.get('limit', 20))
    offset = page * limit
    if volume_ids:
      volumes = re.findall(r'(\d+)', volume_ids)
      logging.debug('Found volume ids: %r', volumes)
      results = []
      for index in range(0, len(volumes), 100):
        volume_page = volumes[index:min([index+100, len(volumes)])]
        results.append(cv.fetch_volume_batch(volume_page))
      results_count = len(results)
      logging.debug('Found volumes: %r' % results)
    elif query:
      results_count, results = cv.search_volume(query, page=page, limit=limit)
      logging.debug('Found volumes: %r' % results)
    if offset + limit > results_count:
      page_end = results_count
    else:
      page_end = offset + limit
    logging.info('Retrieving results %d-%d / %d', offset, page_end,
                 results_count)
    results_page = results[offset:page_end]
    template_values = self.base_template_values()

    template_values.update({
      'query': query,
      'volume_ids': volume_ids,
      'page': page,
      'limit': limit,
      'results': (volume_detail(volume) for volume in results_page),
      'results_count': results_count,
      'page_url': util.StripParam(self.request.url, 'page'),
      'page_count': int(ceil(1.0*results_count/limit)),
    })
    template = self.templates.get_template('volumes_search.html')
    self.response.write(template.render(template_values))

class RefreshVolumes(base.BaseHandler):
    def get(self):
      # When run from cron cycle over all issues weekly
      shard_count=7
      shard=date.today().weekday()
      cv = comicvine.load()
      refresh_callback = partial(
        refresh_volume_shard, int(shard), int(shard_count), comicvine=cv)
      query = Subscription.query(projection=('volume',), distinct=True)
      volume_keys = query.map(refresh_callback)
      update_count = sum([1 for volume in volume_keys if volume])
      status = 'Updated %d/%d volumes' % (
        update_count, len(volume_keys))
      logging.info(status)

app = base.create_app([
  ('/volumes', MainPage),
  ('/volumes/search', Search),
])
