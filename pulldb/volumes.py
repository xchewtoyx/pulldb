# Copyright 2013 Russell Heilling

from datetime import datetime
import logging
from math import ceil

import pycomicvine

from pulldb import base
from pulldb import publishers
from pulldb import subscriptions
from pulldb import users
from pulldb import util
from pulldb.models.admin import Setting
from pulldb.models.volumes import Volume

def volume_key(comicvine_volume, create=True):
  key = None
  user = users.user_key()
  if comicvine_volume:
    volume = Volume.query(
      Volume.identifier==comicvine_volume.id, ancestor=user).get()
    if create and not volume:
      publisher_key = publishers.publisher_key(comicvine_volume.publisher)
      volume = Volume(
        parent=user,
        identifier=comicvine_volume.id,
        publisher=publisher_key,
        last_updated=datetime.min,
      )
    if not hasattr(volume, 'last_updated') or (
        comicvine_volume.date_last_updated > volume.last_updated):
      # Volume is new or has been updated since last
      volume.name=comicvine_volume.name
      volume.issue_count=comicvine_volume.count_of_issues
      volume.site_detail_url=comicvine_volume.site_detail_url
      volume.start_year=comicvine_volume.start_year
      if comicvine_volume.image:
        volume.image = comicvine_volume.image.get('small_url')
      volume.last_updated = comicvine_volume.date_last_updated
      volume.put()
    key = volume.key
  return key

class MainPage(base.BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template = self.templates.get_template('volumes.html')
    self.response.write(template.render(template_values))

class Search(base.BaseHandler):
  def get(self):
    def volume_detail(comicvine_volume):
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
        'subscribed': subscription,
      }

    # TODO(rgh): This should probably be initialised somewhere else
    pycomicvine.api_key = Setting.query(
      Setting.name == 'comicvine_api_key').get().value
    query = self.request.get('q')
    volume_id = self.request.get('volume_id')
    page = int(self.request.get('page', 0))
    limit = int(self.request.get('limit', 20))
    offset = page * limit
    results = []
    if volume_id and volume_id.isdigit():
      results.append(pycomicvine.Volume(
        int(volume_id), field_list=[
          'id', 'name', 'start_year', 'count_of_issues',
          'deck', 'image', 'site_detail_url', 'publisher',
          'date_last_updated']))
    elif query:
      results = pycomicvine.Volumes.search(
        query=query, field_list=[
          'id', 'name', 'start_year', 'count_of_issues',
          'deck', 'image', 'site_detail_url', 'publisher',
          'date_last_updated'])
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
      'volume_id': volume_id,
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
])
