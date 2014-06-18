from collections import defaultdict
import json
import logging

from google.appengine.api import oauth
from google.appengine.ext import ndb

from pulldb import users
from pulldb.api.base import OauthHandler, TaskHandler, JsonModel
from pulldb.base import create_app, Route
from pulldb.models.subscriptions import Subscription, subscription_context
from pulldb.models import volumes

class AddSubscriptions(OauthHandler):
    def post(self):
        user_key = users.user_key(self.user)
        request = json.loads(self.request.body)
        volume_ids = request['volumes']
        results = defaultdict(list)
        keys = [ndb.Key(Subscription, id, parent=user_key) for id in volume_ids]
        # prefetch for efficiency
        ndb.get_multi(keys)
        candidates = []
        for key in keys:
            volume = key.get()
            if volume:
                results['skipped'].append(key.id())
            else:
                candidates.append(key)
        volume_keys = [ndb.Key(volumes.Volume, key.id()) for key in candidates]
        logging.info('%d candidates, %d volumes', len(candidates),
                     len(volume_keys))
        # prefetch for efficiency
        ndb.get_multi(volume_keys)
        subs = []
        for volume_key, candidate in zip(volume_keys, candidates):
            if volume_key.get():
                subs.append(Subscription(
                    key = candidate,
                    volume = volume_key,
                ))
                results['added'].append(candidate.id())
            else:
                results['failed'].append(candidate.id())
        ndb.put_multi(subs)
        response = {
            'status': 200,
            'results': results
        }
        self.response.write(json.dumps(response))

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
    Route(
        '/api/subscriptions/add',
        'pulldb.api.subscriptions.AddSubscriptions',
    ),
    Route('/api/subscriptions/list', 'pulldb.api.subscriptions.ListSubs'),
    Route('/tasks/subscriptions/validate', 'pulldb.api.subscriptions.Validate'),
])
