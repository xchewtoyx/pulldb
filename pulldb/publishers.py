# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

class Publisher(ndb.Model):
  '''Publisher object in datastore.

  Holds publisher data.
  '''
  identifier = ndb.IntegerProperty()
  name = ndb.StringProperty()
  image = ndb.StringProperty()

def publisher_key(comicvine_publisher, create=True):
  key = None
  if comicvine_publisher:
    publisher = Publisher.query(
      Publisher.identifier==comicvine_publisher.id).get()
    if publisher:
      key = publisher.key
    elif create:
      publisher = Publisher(identifier=comicvine_publisher.id, 
                            name=comicvine_publisher.name)
      if comicvine_publisher.image:
        publisher.image=comicvine_publisher.image.get('tiny_url')
      publisher.put_async()
      key = publisher.key
  return key
