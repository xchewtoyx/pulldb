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
  name = ndb.StringProperty()
  start_year = ndb.IntegerProperty()
  publisher = ndb.KeyProperty(kind=publishers.Publisher)
  image = ndb.StringProperty()
  identifier = ndb.IntegerProperty()
  issue_count = ndb.IntegerProperty()
  site_detail_url = ndb.StringProperty()

class MainPage(BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template = self.templates.get_template('volumes.html')
    self.response.write(template.render(template_values))

class Search(BaseHandler):
  def get(self):
    def volume_dict(volume):
      volume_key = fetch_or_store(volume.id, volume)
      publisher_key = volume_key.publisher.get()
      return {
        'volume': volume_key,
        'publisher': publisher_key,
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
        'results': (volume_dict(volume) for volume in results),
        'results_count': len(results),
    })
    template = self.templates.get_template('volumes_search.html')
    self.response.write(template.render(template_values))

def fetch_or_store(identifier, volume):
  volume_key = Volume.query(Volume.identifier==identifier).get()
  if not volume_key:
    publisher = publishers.fetch_or_store(volume.publisher.id, 
                                          volume.publisher)
    volume_key = Volume(identifier=volume.id, name=volume.name,
                        issue_count=volume.count_of_issues, 
                        site_detail_url=volume.site_detail_url,
                        start_year=volume.start_year,
                        image=volume.image['small_url'],
                        publisher=publisher.key)
    volume_key.put()
  return volume_key
    
app = webapp2.WSGIApplication([
    ('/volumes', MainPage),
    ('/volumes/search', Search),
], debug=True)

