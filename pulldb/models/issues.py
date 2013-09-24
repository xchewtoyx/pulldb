# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

class Issue(ndb.Model):
  '''Issue object in datastore.

  Holds issue data.  Parent key should be a volume.
  '''
  identifier = ndb.IntegerProperty()
  pubdate = ndb.DateProperty()
  cover = ndb.BlobProperty()
  image = ndb.StringProperty()
  issue_number = ndb.StringProperty()
  title = ndb.StringProperty()
  site_detail_url = ndb.StringProperty()
