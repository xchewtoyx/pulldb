# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb
import webapp2

import pycomicvine

from pulldb.admin import Setting
from pulldb.base import BaseHandler

class Volume(ndb.Model):
  '''Volume object in datastore.

  Holds volume data.
  '''
  name = ndb.StringProperty()
  start_year = ndb.IntegerProperty()
  publisher = ndb.StringProperty()
  cover = ndb.BlobProperty()

class MainPage(BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template = self.templates.get_template('volumes.html')
    self.response.write(template.render(template_values))

class Search(BaseHandler):
  def get(self):
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
        'results': results,
        'results_count': len(results),
    })
    template = self.templates.get_template('volumes_search.html')
    self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/volumes', MainPage),
    ('/volumes/search', Search),
], debug=True)

