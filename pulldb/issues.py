# Copyright 2013 Russell Heilling

import logging
from math import ceil

import pycomicvine

from google.appengine.ext import ndb

from pulldb import base
from pulldb import util
from pulldb import volumes
from pulldb.models.admin import Setting
from pulldb.models.issues import Issue

def issue_key(comicvine_issue, create=True):
  key = None
  if comicvine_issue:
    issue = Issue.query(Issue.identifier==comicvine_issue.id).get()
    if issue:
      key = issue.key
    elif create:
      volume_key = volumes.volume_key(comicvine_issue.volume)
      issue = Issue(
        parent=volume_key,
        identifier=comicvine_issue.id, 
        title=comicvine_issue.name,
        issue_number=str(comicvine_issue.issue_number), 
        site_detail_url=comicvine_issue.site_detail_url,
        pubdate=comicvine_issue.store_date or comicvine_issue.cover_date)
      if comicvine_issue.image:
        issue.image = comicvine_issue.image.get('small_url')
      issue.put()
      key = issue.key
  return key

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
      volume = volumes.volume_key(comicvine_issue.volume).get()
      # subscription = False
      # subscription_key = subscriptions.subscription_key(volume.key)
      # if subscription_key:
      #   subscription = subscription_key.urlsafe()
      detail = {
        'issue_key': issue.key.urlsafe(),
        'issue': issue,
        'volume': volume,
        'pulled': False,
      }
      logging.info('issue_detail: %r', detail)
      return detail

    logging.debug('Listing issues for volume %s', volume_key)
    # TODO(rgh): This should probably be initialised somewhere else
    pycomicvine.api_key = Setting.query(
      Setting.name == 'comicvine_api_key').get().value
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

app = base.create_app([
    ('/issues', MainPage),
    ('/issues/list/([^/?&]+)', IssueList),
])
