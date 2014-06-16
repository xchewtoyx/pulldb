# Copyright 2013 Russell Heilling
from datetime import datetime
import logging

from google.appengine.api import search
from google.appengine.ext import ndb

from pulldb import publishers
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

def volume_key(comicvine_volume, create=True):
  key = None
  changed = False
  if comicvine_volume:
    volume = Volume.query(
      Volume.identifier==comicvine_volume.id).get()
    if create and not volume:
      logging.info('Creating volume: %r', comicvine_volume)
      publisher_key = publishers.publisher_key(comicvine_volume.publisher)
      volume = Volume(
        identifier=comicvine_volume.id,
        publisher=publisher_key,
        last_updated=datetime.min,
      )
    logging.debug('last update: %r', comicvine_volume.date_last_updated)
    if not hasattr(volume, 'last_updated') or (
        comicvine_volume.date_last_updated > volume.last_updated):
      logging.info('Volume has changes: %r', comicvine_volume)
      # Volume is new or has been info has been updated since last put
      volume.name=comicvine_volume.name
      volume.issue_count=comicvine_volume.count_of_issues
      volume.site_detail_url=comicvine_volume.site_detail_url
      volume.start_year=comicvine_volume.start_year
      if comicvine_volume.image:
        volume.image = comicvine_volume.image.get('small_url')
      volume.last_updated = comicvine_volume.date_last_updated
      changed = True
    if changed:
      logging.info('Saving volume updates: %r', comicvine_volume)
      volume_future = volume.put_async()
    else:
      key = volume.key

    if changed:
      document_fields = [
          search.TextField(name='name', value=volume.name),
          search.NumberField(name='volume_id', value=volume.identifier),
      ]
      if volume.start_year:
        document_fields.append(
          search.NumberField(name='start_year', value=volume.start_year))
      key = volume_future.get_result().key
      volume_doc = search.Document(
        doc_id = key.urlsafe(),
        fields = document_fields)
      try:
        index = search.Index(name="volumes")
        index.put(volume_doc)
      except search.Error as error:
        logging.exception('Put failed: %r', error)
  logging.debug('Found key %r', key)
  return key

@ndb.tasklet
def volume_context(volume):
    publisher = yield volume.publisher.get_async()
    raise ndb.Return({
        'volume': volume,
        'publisher': publisher,
    })
