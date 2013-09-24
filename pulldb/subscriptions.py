# Copyright 2013 Russell Heilling

import logging
import urlparse

from google.appengine.ext import ndb

from pulldb import base
from pulldb import users
from pulldb.models.subscriptions import Subscription

def subscription_key(volume_key, create=False):
  key = None
  user = users.user_key()
  subscription = Subscription.query(Subscription.volume==volume_key,
                                    ancestor=user).get()
  if subscription:
    key = subscription.key
  elif create:
    subscription = Subscription(parent=user, 
                                volume=volume_key)
    subscription.put()
    key = subscription.key
  return key

class MainPage(base.BaseHandler):
  def get(self):
    def subscription_detail(subscription):
      volume = subscription.volume.get()
      return {
        'volume_key': volume.key.urlsafe(),
        'volume': volume,
        'publisher':  volume.publisher.get(),
        'subscribed': subscription,
      }
      
    results = Subscription.query(ancestor=users.user_key())
    template_values = self.base_template_values()
    template_values.update({
        'results': (
          subscription_detail(subscription) for subscription in results),
        'results_count': results.count(),
    })
    template = self.templates.get_template('subscriptions_list.html')
    self.response.write(template.render(template_values))

class AddSub(base.BaseHandler):
  def get(self, volume_key):
    referer = self.request.referer
    volume = ndb.Key(urlsafe=volume_key)
    user = users.user_key().get()
    logging.info(
      'User %s subscribing to volume %s', user.nickname, volume.get().name
    )
    # Add subscription
    subscription_key(volume, create=True)
    # redirect to source
    self.redirect(
      urlparse.urljoin(referer, '#%s' % volume_key))

class RemoveSub(base.BaseHandler):
  def get(self, volume_key):
    logging.warn('Removal not yet supported.')
    referer = self.request.referer
    self.redirect(
      urlparse.urljoin(referer, '#%s' % volume_key))

class UpdateSub(base.BaseHandler):
  def post(self):
    pass

app = base.create_app([
    (r'/subscriptions$', MainPage),
    (r'/subscriptions/add/([^/]+)', AddSub),
    (r'/subscriptions/remove/([^/])+', RemoveSub),
    (r'/subscriptions/update/([^/])+', UpdateSub),
])  
