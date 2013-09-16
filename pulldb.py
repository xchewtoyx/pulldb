import os

from google.appengine.api import users

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(
    os.path.join(os.path.dirname(__file__), 'template')),
  extensions=['jinja2.ext.autoescape'])

class MainPage(webapp2.RequestHandler):
  def get(self):
    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'url': url,
      'url_linktext': url_linktext,
    }

    template = JINJA_ENVIRONMENT.get_template('index.html')
    self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
