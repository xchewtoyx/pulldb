# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

from pulldb.users import user_key

class Subscription(ndb.Model):
  '''Subscription object in datastore.

  Holds subscription data. Parent should be User.
  '''
  start_date = ndb.DateProperty()
  volume = ndb.KeyProperty(kind='Volume')

def subscription_key(volume_key, create=False):
  key = None
  user = user_key()
  subscription = Subscription.query(Subscription.volume==volume_key,
                                    ancestor=user).get()
  if subscription:
    key = subscription.key
  elif create:
    subscription = Subscription(parent=user, 
                                volume=volume_key)
    subscription.put()
    key = user.key
  return key

  
