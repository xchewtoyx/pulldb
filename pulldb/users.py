# Copyright 2013 Russell Heilling
import logging

from google.appengine.api import users
from google.appengine.ext import ndb

from pulldb import base
from pulldb import session
from pulldb.publishers import Publisher

import webapp2 

class User(ndb.Model):
  '''User object in datastore.

  Holds the email and ID of the users that have a pull-list.
  '''
  userid = ndb.StringProperty()
  image = ndb.StringProperty()
  nickname = ndb.StringProperty()
  oauth_token = ndb.StringProperty()
  publisher = ndb.KeyProperty(key=Publisher)

class Profile(session.SessionHandler):
  def get(self):
    user = users.get_current_user()
    user_key = User.query(User.userid == user.user_id()).get()
    if not user_key:
      logging.info('Adding user to datastore: %s', user.nickname())
      user_key = User(userid=user.user_id(), nickname=user.nickname())
      user_key.put()
    template_values = self.base_template_values()
    template_values.update({
        'user': user_key,
    })
    template = self.templates.get_template('users_profile.html')
    self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([
    ('/users/me', Profile),
], debug=True)
