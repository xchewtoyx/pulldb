# Copyright 2013 Russell Heilling
import logging

from google.appengine.api import users

from pulldb import base
from pulldb import session
from pulldb.models.users import User

class Profile(session.SessionHandler):
  def get(self):
    app_user = users.get_current_user()
    template_values = self.base_template_values()
    template_values.update({
        'user': user_key(app_user).get(),
    })
    template = self.templates.get_template('users_profile.html')
    self.response.write(template.render(template_values))

def user_key(app_user=users.get_current_user(), create=True):
  key = None
  user = User.query(User.userid == app_user.user_id()).get()
  if user:
    key = user.key
  elif create:
    logging.info('Adding user to datastore: %s', app_user.nickname())
    user = User(userid=app_user.user_id(), 
                nickname=app_user.nickname())
    user.put()
    key = user.key
  return user.key

app = base.create_app([
    ('/users/me', Profile),
])
