# Copyright 2013 Russell Heilling
import logging

from google.appengine.ext import ndb
import webapp2

from pulldb.base import BaseHandler

class Setting(ndb.Model):
  '''Setting object in datastore.

  Holds settings data.
  '''
  name = ndb.StringProperty()
  value = ndb.StringProperty()

class MainPage(BaseHandler):
  def get(self):
    template_values = {
      'comicvine_api_key': Setting.query(
        Setting.name == 'comicvine_api_key').get(),
    }
    template_values.update(self.get_user_info())
    template = self.templates.get_template('admin.html')
    self.response.write(template.render(template_values))

class Settings(BaseHandler):
  def post(self):
    new_api_key = self.request.get('comicvine_api_key')
    comicvine_api_key = Setting.query(
      Setting.name == 'comicvine_api_key').get()
    if comicvine_api_key:
      comicvine_api_key.value = new_api_key
    else:
      comicvine_api_key = Setting(
        name='comicvine_api_key', value=new_api_key)
    comicvine_api_key.put()
    self.redirect('/admin')

app = webapp2.WSGIApplication([
    ('/admin', MainPage),
    ('/admin/settings', Settings),
], debug=True)
