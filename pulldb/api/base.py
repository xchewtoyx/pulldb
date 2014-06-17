from datetime import date, time, datetime
import json
import logging

from google.appengine.api import oauth
from google.appengine.api import users
from google.appengine.ext import ndb

from pulldb.base import BaseHandler

class JsonModel(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, ndb.Key):
            value = value.urlsafe()
        if isinstance(value, ndb.Model):
            return value.to_dict()
        if isinstance(value, (datetime, date, time)):
            return str(value)

class OauthHandler(BaseHandler):
    def dispatch(self):
        self.scope = 'https://www.googleapis.com/auth/userinfo.email'
        try:
            user = oauth.get_current_user(self.scope)
        except oauth.OAuthRequestError, e:
            logging.warn('Unable to determine user for request')
            self.abort(401)
        self.user = user
        logging.info('Request authorized by %r', user)
        BaseHandler.dispatch(self)

class TaskHandler(BaseHandler):
    def dispatch(self):
        self.scope = 'https://www.googleapis.com/auth/userinfo.email'
        user = users.get_current_user()
        if not user and 'X-Appengine-Cron' in self.request.headers:
            user = users.User('russell+cron@heilling.net')
        try:
            if not user:
                user = oauth.get_current_user(self.scope)
        except oauth.OAuthRequestError, e:
            logging.warn('Unable to determine user for request')
            self.abort(401)
        self.user = user
        logging.info('Request authorized by %r', user)
        BaseHandler.dispatch(self)
