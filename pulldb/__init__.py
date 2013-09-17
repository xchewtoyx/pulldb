import os

from google.appengine.api import users

import jinja2
import webapp2

from pulldb import index

application = webapp2.WSGIApplication([
    ('/', index.MainPage),
], debug=True)
