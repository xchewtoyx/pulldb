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
    template_values = self.base_template_values()
    template_values.update({
      'comicvine_api_key': Setting.query(
          Setting.name == 'comicvine_api_key').get(),
      'session_store_key': Setting.query(
          Setting.name == 'session_store_key').get(),
    })
    template = self.templates.get_template('admin.html')
    self.response.write(template.render(template_values))

class Settings(BaseHandler):
  def set_key(self, name, value):
    setting_key = Setting.query(Setting.name == name).get()
    if setting_key:
      setting_key.value = value
    else:
      setting_key = Setting(name=name, value=value)
    setting_key.put()

  def post(self):
    comicvine_api_key = self.request.get('comicvine_api_key')
    session_store_key = self.request.get('session_store_key')
    self.set_key('comicvine_api_key', comicvine_api_key)
    self.set_key('session_store_key', session_store_key)
    self.redirect('/admin')

def get_setting(name):
  value = Session.query(Setting.name==name).get().value
  return value

app = webapp2.WSGIApplication([
    ('/admin', MainPage),
    ('/admin/settings', Settings),
], debug=True)
