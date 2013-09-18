# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

class Volume(ndb.Model):
  '''Volume object in datastore.

  Holds volume data.
  '''
  name = ndb.StringProperty()
  start_year = ndb.IntegerProperty()
  publisher = ndb.StringProperty()
  cover = ndb.BlobProperty()
