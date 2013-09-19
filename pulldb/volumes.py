# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

import webapp2

import pycomicvine

from pulldb.admin import Setting
from pulldb.base import BaseHandler
from pulldb import publishers

class Volume(ndb.Model):
  '''Volume object in datastore.

  Holds volume data.
  '''
  identifier = ndb.IntegerProperty()
  image = ndb.StringProperty()
  issue_count = ndb.IntegerProperty()
  name = ndb.StringProperty()
  publisher = ndb.KeyProperty(kind=publishers.Publisher)
  site_detail_url = ndb.StringProperty()
  start_year = ndb.IntegerProperty()

class MainPage(BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template = self.templates.get_template('volumes.html')
    self.response.write(template.render(template_values))

class Search(BaseHandler):
  def get(self):
    def volume_detail(comicvine_volume):
      volume = fetch_or_store(comicvine_volume).get()
      publisher_key = volume.publisher
      publisher = None
      if publisher_key:
        publisher = publisher_key.get()
      return {
        'volume': volume,
        'publisher': publisher,
      }

    pycomicvine.api_key = Setting.query(
      Setting.name == 'comicvine_api_key').get().value
    query = self.request.get('q')
    results = []
    if query:
      results = pycomicvine.Volumes.search(
        query=query, field_list=[
          'id', 'name', 'start_year', 'count_of_issues',
          'deck', 'image', 'site_detail_url', 'publisher'])
    template_values = self.base_template_values()
    template_values.update({
        'query': query,
        'results': (volume_detail(volume) for volume in results if volume),
        'results_count': len(results),
    })
    template = self.templates.get_template('volumes_search.html')
    self.response.write(template.render(template_values))

def fetch_or_store(comicvine_volume):
  if comicvine_volume:
    volume = Volume.query(Volume.identifier==comicvine_volume.id).get()
    if not volume:
      publisher = publishers.fetch_or_store(comicvine_volume.publisher) 
      volume = Volume(
        identifier=comicvine_volume.id, 
        name=comicvine_volume.name,
        issue_count=comicvine_volume.count_of_issues, 
        site_detail_url=comicvine_volume.site_detail_url,
        start_year=comicvine_volume.start_year,
        image=comicvine_volume.image['small_url'],
        publisher=publisher)
      volume.put()
    volume_key = volume.key
  else:
    volume_key = None
  return volume_key
    
app = webapp2.WSGIApplication([
    ('/volumes', MainPage),
    ('/volumes/search', Search),
], debug=True)
