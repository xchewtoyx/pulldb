# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

from pulldb.models.properties import ImageProperty

class Publisher(ndb.Model):
  '''Publisher object in datastore.

  Holds publisher data.
  '''
  identifier = ndb.IntegerProperty()
  name = ndb.StringProperty()
  image = ImageProperty()
