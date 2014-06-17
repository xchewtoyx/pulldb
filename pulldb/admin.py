# Copyright 2013 Russell Heilling
from google.appengine.ext import ndb

from pulldb import base
from pulldb.models.admin import Setting

class MainPage(base.BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template_values.update({
      'comicvine_api_key': Setting.query(
          Setting.name == 'comicvine_api_key').get(),
      'session_store_key': Setting.query(
          Setting.name == 'session_store_key').get(),
      'update_shards_key': Setting.query(
          Setting.name == 'update_shards_key').get()
    })
    template = self.templates.get_template('admin.html')
    self.response.write(template.render(template_values))

class Settings(base.BaseHandler):
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
    update_shards_key = self.request.get('update_shards_key')
    self.set_key('comicvine_api_key', comicvine_api_key)
    self.set_key('session_store_key', session_store_key)
    self.set_key('update_shards_key', update_shards_key)
    self.redirect('/admin')

def get_setting(name):
  value = Setting.query(Setting.name==name).get().value
  return value

app = base.create_app([
    ('/admin', MainPage),
    ('/admin/settings', Settings),
])
