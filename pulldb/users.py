# Copyright 2013 Russell Heilling
import logging

from google.appengine.api import users
from google.appengine.ext import ndb

from pulldb import session

import webapp2 

class User(ndb.Model):
  '''User object in datastore.

  Holds the email and ID of the users that have a pull-list.
  '''
  userid = ndb.StringProperty()
  image = ndb.StringProperty()
  nickname = ndb.StringProperty()
  oauth_token = ndb.StringProperty()

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

app = webapp2.WSGIApplication([
    ('/users/me', Profile),
], debug=True)
