# Copyright 2013 Russell Heilling
from datetime import datetime, date
import logging

from google.appengine.api import search
from google.appengine.ext import ndb

from pulldb.models import comicvine
from pulldb.models.properties import ImageProperty
from pulldb.models import volumes

class Issue(ndb.Model):
  '''Issue object in datastore.

  Holds issue data.  Parent key should be a volume.
  '''
  identifier = ndb.IntegerProperty()
  pubdate = ndb.DateProperty()
  cover = ndb.BlobProperty()
  image = ImageProperty()
  issue_number = ndb.StringProperty()
  last_updated = ndb.DateTimeProperty(default=datetime.min)
  title = ndb.StringProperty()
  site_detail_url = ndb.StringProperty()
  file_path = ndb.StringProperty()

@ndb.tasklet
def refresh_issue_shard(shard, shard_count, subscription):
    volume = yield subscription.volume.get_async()
    if volume.identifier % shard_count == shard:
        comicvine_volume = comicvine.Volume(volume.identifier)
        comicvine_issues = list(comicvine_volume.issues)
        issues = []
        for index in range(0, len(comicvine_issues), 100):
            ids = '|'.join(
                [str(issue.id) for issue in comicvine_issues[
                    index:max([len(comicvine_issues), index+100])]])
            issue_page = comicvine.Issues(filter="id:%s" % ids, all=True)
            for issue in issue_page:
                issues.append(issue_key(
                    issue, volume_key=volume.key, create=True, reindex=True))
        raise ndb.Return(issues)

def issue_key(comicvine_issue, volume_key=None, create=True, reindex=False):
  key = None
  changed = False
  if comicvine_issue:
    issue = Issue.query(Issue.identifier==comicvine_issue.id).get()

    if create and not issue:
      if not volume_key:
        volume_key = volumes.volume_key(comicvine_issue.volume)
      issue = Issue(
        parent=volume_key,
        identifier=comicvine_issue.id,
        last_updated=datetime.min
      )
    if not hasattr(issue, 'last_updated') or (
        comicvine_issue.date_last_updated > issue.last_updated):
      volume = volume_key.get()
      issue.name='%s %s' % (
        volume.name,
        comicvine_issue.issue_number,
      )
      # Use _fields member rather than accessor attributes to
      # avoid kicking off unnecessary api requests
      data = comicvine_issue._fields
      issue.title = data.get('name')
      issue.issue_number=str(data.get('issue_number'))
      issue.site_detail_url=data.get('site_detail_url')
      pubdate = data.get('store_date') or data.get('cover_date')
      if isinstance(pubdate, date):
        issue.pubdate=pubdate
      if 'image' in data:
        issue.image = data['image'].get('small_url')
      changed = True
    if changed:
      logging.info('Saving issue updates: %r', comicvine_issue)
      key = issue.put()
    else:
      key = issue.key

    if changed or reindex:
      document_fields = [
          search.TextField(name='title', value=issue.title),
          search.TextField(name='name', value=issue.name),
          search.TextField(name='issue_number', value=issue.issue_number),
          search.NumberField(name='issue_id', value=issue.identifier),
      ]
      if isinstance(issue.pubdate, date):
        document_fields.append(
          search.DateField(name='pubdate', value=issue.pubdate)
        )
      volume_doc = search.Document(
        doc_id = key.urlsafe(),
        fields = document_fields)
      try:
        index = search.Index(name="issues")
        index.put(volume_doc)
      except search.Error as error:
        logging.exception('Put failed: %r', error)

  return key

@ndb.tasklet
def issue_context(issue):
    publisher = yield volume.publisher.get_async()
    raise ndb.Return({
        'volume': volume,
        'publisher': publisher,
    })
