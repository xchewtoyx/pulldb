import os
import site

from google.appengine.api import users

import jinja2
import webapp2

from pulldb import index
from pulldb.util import AppRoot

site.addsitedir(os.path.join(AppRoot(), 'site-packages'))

application = webapp2.WSGIApplication([
    ('/', index.MainPage),
], debug=True)
