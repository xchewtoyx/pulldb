# Copyright 2013 Russell Heilling

from datetime import datetime

from google.appengine.ext import ndb

from pulldb.models import publishers
from pulldb.models.properties import ImageProperty

class Volume(ndb.Model):
  '''Volume object in datastore.

  Holds volume data.
  '''
  identifier = ndb.IntegerProperty()
  image = ImageProperty()
  issue_count = ndb.IntegerProperty()
  last_updated = ndb.DateTimeProperty(default=datetime.min)
  name = ndb.StringProperty()
  publisher = ndb.KeyProperty(kind=publishers.Publisher)
  site_detail_url = ndb.StringProperty()
  start_year = ndb.IntegerProperty()

@ndb.tasklet
def volume_context(volume):
    publisher = yield volume.publisher.get_async()
    raise ndb.Return({
        'volume': volume,
        'publisher': publisher,
    })
