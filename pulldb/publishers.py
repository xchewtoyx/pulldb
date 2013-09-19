# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

class Publisher(ndb.Model):
  '''Publisher object in datastore.

  Holds publisher data.
  '''
  identifier = ndb.IntegerProperty()
  name = ndb.StringProperty()
  image = ndb.StringProperty()

def fetch_or_store(comicvine_publisher):
  if comicvine_publisher:
    publisher = Publisher.query(
      Publisher.identifier==comicvine_publisher.id).get()
    if not publisher:
      publisher = Publisher(identifier=comicvine_publisher.id, 
                            name=comicvine_publisher.name)
      if comicvine_publisher.image:
        publisher.image=comicvine_publisher.image.get('tiny_url')
      publisher.put()
    publisher_key = publisher.key
  else:
    publisher_key = None
  return publisher_key
