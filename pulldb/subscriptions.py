# Copyright 2013 Russell Heilling

from google.appengine.ext import ndb

from pulldb import base
from pulldb import users

class Subscription(ndb.Model):
  '''Subscription object in datastore.

  Holds subscription data. Parent should be User.
  '''
  start_date = ndb.DateProperty()
  volume = ndb.KeyProperty(kind='Volume')

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
    key = user.key
  return key

class MainPage(base.BaseHandler):
  def get(self):
    def subscription_detail(subscription):
      volume = subscription.volume.get()
      return {
        'volume': volume,
        'publisher':  volume.publisher.get(),
        'subscription': subscription,
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
  def post(self):
    pass

class RemoveSub(base.BaseHandler):
  def post(self):
    pass

class UpdateSub(base.BaseHandler):
  def post(self):
    pass

app = base.create_app([
    ('/subscriptions', MainPage),
    ('/subscriptions/add', AddSub),
    ('/subscriptions/remove', RemoveSub),
    ('/subscriptions/update', UpdateSub),
])  
