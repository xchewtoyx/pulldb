# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

from pulldb import base
from pulldb import session

import webapp2 

class User(ndb.Model):
  '''User object in datastore.

  Holds the email and ID of the users that have a pull-list.
  '''
  userid = ndb.IntegerProperty()
  image = ndb.StringProperty()
  email = ndb.StringProperty()
  oauth_token = ndb.StringProperty()

class Profile(session.SessionHandler):
  def get(self):
    template_values = self.base_template_values()
    template_values.update({
    })
    template = self.templates.get_template('users_profile.html')
    self.response.write(template.render(template_values))

class Register(base.BaseHandler):
  def post(self):
    self.redirect('/users')

app = webapp2.WSGIApplication([
    ('/users/me', Profile),
    ('/users/register', Register),
], debug=True)
