# Copyright 2013 Russell Heilling
from functools import partial
import logging
from math import ceil

from google.appengine.ext import ndb

from pulldb import base
from pulldb import util
from pulldb.api.issues import RefreshShard
from pulldb.models.admin import Setting
from pulldb.models import comicvine
from pulldb.models.issues import Issue, issue_key, refresh_issue_shard
from pulldb.models.subscriptions import Subscription
from pulldb.models import volumes

class MainPage(base.BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template = self.templates.get_template('issues.html')
    self.response.write(template.render(template_values))

class IssueList(base.BaseHandler):
  def get(self, volume_key=None):
    def issue_detail(comicvine_issue):
      logging.debug('Creating detail for %r', comicvine_issue)
      volume = volumes.volume_key(comicvine_issue['volume']).get()
      issue = issue_key(comicvine_issue, volume_key=volume.key).get()
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
    cv = comicvine.load()
    page = int(self.request.get('page', 0))
    limit = int(self.request.get('limit', 20))
    offset = page * limit
    results = []
    if volume_key:
      volume = ndb.Key(urlsafe=volume_key).get()
      volume_detail = cv.fetch_volume(volume.identifier)
    issues = volume_detail['issues']
    issue_count = len(issues)
    page_end = min([len(issues), offset + limit])
    issue_ids = []
    for issue in volume_detail['issues'][offset:page_end]:
      issue_ids.append(issue['id'])
    results = cv.fetch_issue_batch(issue_ids)
    logging.info('Retrieving results %d-%d / %d', offset, page_end,
                 issue_count)
    template_values = self.base_template_values()

    template_values.update({
      'page': page,
      'limit': limit,
      'results': (issue_detail(issue) for issue in results),
      'results_count': issue_count,
      'page_url': util.StripParam(self.request.url, 'page',
                                  replacement='___'),
      'page_count': int(ceil(1.0*issue_count/limit)),
    })
    logging.debug('Rendering template %s using values %r',
                  'issues_list.html', template_values)
    template = self.templates.get_template('issues_list.html')
    self.response.write(template.render(template_values))

app = base.create_app([
  ('/issues', MainPage),
  ('/issues/list/([^/?&]+)', IssueList),
])
