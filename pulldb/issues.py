# Copyright 2013 Russell Heilling
from datetime import date, datetime
from functools import partial
import logging
from math import ceil

import pycomicvine

from google.appengine.ext import ndb

from pulldb import base
from pulldb import util
from pulldb.api.issues import RefreshShard
from pulldb.models.admin import Setting
from pulldb.models import comicvine
from pulldb.models.issues import Issue, issue_key, refresh_issue_shard
from pulldb.models.volumes import volume_key

class MainPage(base.BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template = self.templates.get_template('issues.html')
    self.response.write(template.render(template_values))

class IssueList(base.BaseHandler):
  def get(self, volume_key=None):
    def issue_detail(comicvine_issue):
      logging.debug('Creating detail for %r', comicvine_issue)
      issue = issue_key(comicvine_issue).get()
      volume = volume_key(comicvine_issue.volume).get()
      # subscription = False
      # subscription_key = subscriptions.subscription_key(volume.key)
      # if subscription_key:
      #   subscription = subscription_key.urlsafe()
      detail = {
        'issue_key': issue.key.urlsafe(),
        'issue': issue,
        'volume': volume,
      }
      logging.info('issue_detail: %r', detail)
      return detail

    logging.debug('Listing issues for volume %s', volume_key)
    comicvine.load()
    page = int(self.request.get('page', 0))
    limit = int(self.request.get('limit', 20))
    offset = page * limit
    results = []
    if volume_key:
      volume = ndb.Key(urlsafe=volume_key).get()
      volume_filter = 'volume:%d' % volume.identifier
      results = pycomicvine.Issues(
        filter=volume_filter, field_list=[
          'id', 'title', 'store_date', 'cover_date',
          'issue_number', 'image', 'site_detail_url', 'volume'])
    if offset + limit > len(results):
      page_end = len(results)
    else:
      page_end = offset + limit
    logging.info('Retrieving results %d-%d / %d', offset, page_end,
                 len(results))
    results_page = results[offset:page_end]
    template_values = self.base_template_values()

    template_values.update({
      'page': page,
      'limit': limit,
      'results': (issue_detail(issue) for issue in results_page),
      'results_count': len(results),
      'page_url': util.StripParam(self.request.url, 'page',
                                  replacement='___'),
      'page_count': int(ceil(1.0*len(results)/limit)),
    })
    logging.debug('Rendering template %s using values %r',
                  'issues_list.html', template_values)
    template = self.templates.get_template('issues_list.html')
    self.response.write(template.render(template_values))

class RefreshShard(base.BaseHandler):
    def get(self):
      # When run from cron cycle over all issues
      shard_count=24 * 7
      shard=datetime.today().hour + 24 * date.today().weekday()
      comicvine.load()
      refresh_callback = partial(
        refresh_issue_shard, int(shard), int(shard_count))
      query = Subscription.query(projection=('volume',), distinct=True)
      volume_keys = query.map(refresh_callback)
      volume_count = sum([1 for volume in volume_keys if volume])
      issue_count = sum([len(volume) for volume in volume_keys if volume])
      status = 'Updated %d issues in %d/%d volumes' % (
        issue_count, update_count, len(volume_keys))
      logging.info(status)

app = base.create_app([
  ('/issues', MainPage),
  ('/issues/list/([^/?&]+)', IssueList),
  ('/tasks/issues/refresh', RefreshShard),
])
