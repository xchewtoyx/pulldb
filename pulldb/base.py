import os

from google.appengine.api import users

import jinja2
import webapp2

from pulldb import util

class BaseHandler(webapp2.RequestHandler):
  def __init__(self, *args, **kwargs):
    super(BaseHandler, self).__init__(*args, **kwargs)
    self.templates = jinja2.Environment(
      loader=jinja2.FileSystemLoader(
        os.path.join(util.AppRoot(), 'template')),
      extensions=['jinja2.ext.autoescape'])
  
  def get_user_info(self):
    user = users.get_current_user()
    if user:
      user_info = {
        'user_info_url': users.create_logout_url(self.request.uri),
        'user_info_text': 'Logout',
        'user_info_name': user.nickname(),
      }
    else:
      user_info = {
        'user_info_url': users.create_login_url(self.request.uri),
        'user_info_text': 'Login',
        'user_info_name': None,
      }
    return user_info

