# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

class User(ndb.Model):
  '''User object in datastore.

  Holds the email and ID of the users that have a pull-list.
  '''
  userid = ndb.StringProperty()
  image = ndb.StringProperty()
  nickname = ndb.StringProperty()
  oauth_token = ndb.StringProperty()
