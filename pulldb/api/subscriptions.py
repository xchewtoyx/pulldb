from collections import defaultdict
import json
import logging

from dateutil.parser import parse as parse_date

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

class UpdateSubs(OauthHandler):
    def post(self):
        user_key = users.user_key(self.user)
        request = json.loads(self.request.body)
        updates = request.get('updates', [])
        results = defaultdict(list)
        sub_keys = [
            ndb.Key(Subscription, key, parent=user_key) for key in updates
        ]
        # bulk fetch to populate the cache
        ndb.get_multi(sub_keys)
        updated_subs = []
        for key in sub_keys:
            subscription = key.get()
            if subscription:
                start_date = parse_date(updates.get(key.id())).date()
                if start_date == subscription.start_date:
                    results['skipped'].append(key.id())
                else:
                    subscription.start_date = start_date
                    updated_subs.append(subscription)
                    results['updated'].append(key.id())
            else:
                # no such subscription
                logging.debug('Not subscribed to volume %r', key)
                results['failed'].append(key.id())
        ndb.put_multi(updated_subs)
        response = {
            'status': 200,
            'results': results
        }
        self.response.write(json.dumps(response))

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
    Route('/api/subscriptions/update', 'pulldb.api.subscriptions.UpdateSubs'),
    Route('/tasks/subscriptions/validate', 'pulldb.api.subscriptions.Validate'),
])
