# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

from pulldb.models import publishers

class Volume(ndb.Model):
  '''Volume object in datastore.

  Holds volume data.
  '''
  identifier = ndb.IntegerProperty()
  image = ndb.StringProperty()
  issue_count = ndb.IntegerProperty()
  name = ndb.StringProperty()
  publisher = ndb.KeyProperty(kind=publishers.Publisher)
  site_detail_url = ndb.StringProperty()
  start_year = ndb.IntegerProperty()
