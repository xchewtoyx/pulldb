import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(
    os.path.join(os.path.dirname(__file__), 'template')),
  extensions=['jinja2.ext.autoescape'])

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
  return ndb.Key('Guestbook', guestbook_name)

class Greeting(ndb.Model):
  author = ndb.UserProperty()
  content = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):
  def get(self):
    guestbook_name = self.request.get('guestbook_name',
                                      DEFAULT_GUESTBOOK_NAME)

    greetings_query = Greeting.query(
      ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
    greetings = greetings_query.fetch(10)

    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'greetings': greetings,
      'guestbook_name': urllib.quote_plus(guestbook_name),
      'url': url,
      'url_linktext': url_linktext,
    }

    template = JINJA_ENVIRONMENT.get_template('guestbook.html')
    self.response.write(template.render(template_values))

class Guestbook(webapp2.RequestHandler):
  def post(self):
    guestbook_name = self.request.get(
      'gestbook_name', DEFAULT_GUESTBOOK_NAME)
    greeting = Greeting(parent=guestbook_key(guestbook_name))

    if users.get_current_user():
      greeting.author = users.get_current_user()

    greeting.content = self.request.get('content')
    greeting.put()

    query_params = {'guestbook_name': guestbook_name}
    self.redirect('/gb/?' + urllib.urlencode(query_params))

application = webapp2.WSGIApplication([
    ('/gb/', MainPage),
    ('/gb/sign', Guestbook),
], debug=True)
                                   
