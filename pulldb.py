import os

from google.appengine.api import users

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(
    os.path.join(os.path.dirname(__file__), 'template')),
  extensions=['jinja2.ext.autoescape'])

class BaseHandler(webapp2.RequestHandler):
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


class MainPage(BaseHandler):
  def get(self):
    template_values = {
    }
    template_values.update(self.get_user_info())
    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
