import json
import logging

from google.appengine.api import oauth
from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models.subscriptions import Subscription, subscription_context

class ListSubs(OauthHandler):
    def get(self):
        user_key = users.user_key(oauth.get_current_user(self.scope))
        query = Subscription.query(ancestor=user_key)
        results = query.map(subscription_context)
        self.response.write(JsonModel().encode(list(results)))

app = create_app([
    Route('/api/subscriptions/list', 'pulldb.api.subscriptions.ListSubs'),
])
