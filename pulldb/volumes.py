# Copyright 2013 Russell Heilling

import logging
from math import ceil

import pycomicvine

from pulldb import base
from pulldb import publishers
from pulldb import subscriptions
from pulldb import util
from pulldb.models.admin import Setting
from pulldb.models.volumes import Volume

def volume_key(comicvine_volume, create=True):
  key = None
  if comicvine_volume:
    volume = Volume.query(Volume.identifier==comicvine_volume.id).get()
    if volume:
      key = volume.key
    elif create:
      publisher_key = publishers.publisher_key(comicvine_volume.publisher)
      volume = Volume(
        identifier=comicvine_volume.id, 
        name=comicvine_volume.name,
        issue_count=comicvine_volume.count_of_issues, 
        site_detail_url=comicvine_volume.site_detail_url,
        start_year=comicvine_volume.start_year,
        publisher=publisher_key)
      if comicvine_volume.image:
        volume.image = comicvine_volume.image.get('small_url')
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
    page = int(self.request.get('page', 0))
    limit = int(self.request.get('limit', 20))
    offset = page * limit
    results = []
    if query:
      results = pycomicvine.Volumes.search(
        query=query, field_list=[
          'id', 'name', 'start_year', 'count_of_issues',
          'deck', 'image', 'site_detail_url', 'publisher'])
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
