# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

class Subscription(ndb.Model):
  '''Subscription object in datastore.

  Holds subscription data. Parent should be User.
  '''
  start_date = ndb.DateProperty()
  volume = ndb.KeyProperty(kind='Volume')
