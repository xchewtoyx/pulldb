import json
import logging

from google.appengine.api import oauth
from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, TaskHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models.subscriptions import Subscription, subscription_context

class ListSubs(OauthHandler):
    def get(self):
        user_key = users.user_key(self.user)
        query = Subscription.query(ancestor=user_key)
        results = query.map(subscription_context)
        self.response.write(JsonModel().encode(list(results)))

class Validate(TaskHandler):
    @ndb.tasklet
    def drop_invalid(self, subscription):
        volume = yield subscription.volume.get_async()
        if not volume:
            deleted = yield subscription.key.delete_async()
            raise ndb.Return(True)

    def get(self):
        query = Subscription.query()
        results = query.map(self.drop_invalid)
        deleted = sum(1 for deleted in results if deleted)
        self.response.write(json.dumps({
            'status': 200,
            'seen': len(results),
            'deleted': deleted,
        }))

app = create_app([
    Route('/api/subscriptions/list', 'pulldb.api.subscriptions.ListSubs'),
    Route('/tasks/subscriptions/validate', 'pulldb.api.subscriptions.Validate'),
])
