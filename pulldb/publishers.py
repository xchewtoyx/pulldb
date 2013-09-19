# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

class Publisher(ndb.Model):
  '''Publisher object in datastore.

  Holds publisher data.
  '''
  identifier = ndb.IntegerProperty()
  name = ndb.StringProperty()
  image = ndb.StringProperty()

def fetch_or_store(identifier, publisher):
  publisher_key = Publisher.query(Publisher.identifier==identifier).get()
  if not publisher_key:
    publisher_key = Publisher(identifier=publisher.id, name=publisher.name,
                              image=publisher.image['tiny_url'])
    publisher_key.put()
  return publisher_key
