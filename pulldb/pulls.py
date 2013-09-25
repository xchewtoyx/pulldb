# Copyright 2013 Russell Heilling

import logging
import urlparse

from google.appengine.ext import ndb

from pulldb import base
from pulldb import users
from pulldb.models.pulls import Pull
from pulldb.models.subscriptions import Subscription
from pulldb.models.volumes import Volume

def pull_key(issue_key, create=False):
  key = None
  user_key = users.user_key()
  volume_key = issue_key.parent()
  subscription_key = Subscription.query(Subscription.volume==volume_key, 
                                        ancestor=user_key)
  pull = Pull.query(Pull.issue==issue_key,
                    ancestor=subscription_key).get()
  if pull:
    key = pull.key
  elif create:
    pull = Pull(parent=subscription_key, 
                issue=issue_key)
    pull.put()
    key = pull.key
  return key

class MainPage(base.BaseHandler):
  def get(self):
    def pull_detail(pull):
      issue = pull.issue.get()
      return {
        'issue_key': issue.key.urlsafe(),
        'issue': issue,
        'pulled': True,
      }
      
    results = Pull.query(ancestor=users.user_key())
    template_values = self.base_template_values()
    template_values.update({
        'results': (pull_detail(pull) for pull in results),
        'results_count': results.count(),
    })
    template = self.templates.get_template('pulls_list.html')
    self.response.write(template.render(template_values))

class AddPull(base.BaseHandler):
  def get(self, issue_key):
    referer = self.request.referer
    issue = ndb.Key(urlsafe=issue_key)
    user = users.user_key().get()
    logging.info(
      'User %s subscribing to issue %s', user.nickname, issue.get().title
    )
    pull_key(issue, create=True)
    # redirect to source
    self.redirect(
      urlparse.urljoin(referer, '#%s' % issue_key))

class RemovePull(base.BaseHandler):
  def get(self, issue_key):
    logging.warn('Removal not yet supported.')
    referer = self.request.referer
    self.redirect(
      urlparse.urljoin(referer, '#%s' % issue_key))

class UpdatePull(base.BaseHandler):
  def post(self):
    pass

app = base.create_app([
    (r'/pulls$', MainPage),
    (r'/pulls/add/([^/]+)', AddPull),
    (r'/pulls/remove/([^/])+', RemovePull),
    (r'/pulls/update/([^/])+', UpdatePull),
])  
