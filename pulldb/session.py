import webapp2
from webapp2_extras import sessions

from pulldb import admin
from pulldb import base

class ConfiguredSession(sessions.SessionStore):
  def __init__(self, *args, **kwargs):
    config = {
      'secret_key': admin.get_setting('session_store_key'),
    }
    kwargs['config'] = config
    super(ConfiguredSession, self).__init__(*args, **kwargs)

class SessionHandler(base.BaseHandler):
  def dispatch(self):
    self.session_store = sessions.get_store(factory=ConfiguredSession,
                                            request=self.request)
    try:
      webapp2.RequestHandler.dispatch(self)
    finally:
      self.session_store.save_sessions(self.response)

  @webapp2.cached_property
  def session(self):
    return self.session_store.get_session()
