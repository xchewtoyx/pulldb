import os

from google.appengine.api import users

import jinja2
import webapp2
from webapp2_extras import sessions

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
        'user_is_admin': users.is_current_user_admin(),
      }
    else:
      user_info = {
        'user_info_url': users.create_login_url(self.request.uri),
        'user_info_text': 'Login',
        'user_info_name': None,
        'user_is_admin': False,
      }
    return user_info

  def base_template_values(self):
    template_values = {
      'url_path': self.request.path,
    }
    template_values.update(self.get_user_info())
    return template_values
