# Copyright 2013 Russell Heilling

import logging
import os
import sys
import urllib
import urlparse

import pulldb

def AppRoot():
  '''Find the application root.
  
  The application root should be in the python path.  Check for an
  entry in the path that is in the path to the application module and
  contains an 'app.yaml' file.
  '''
  app_root = None
  module_path = pulldb.__file__
  for path in sys.path:
    prefix = os.path.commonprefix([path, module_path])
    if (prefix == path and 
        os.path.exists(os.path.join(prefix, 'app.yaml'))):
      app_root = prefix
      break
  if not app_root:
    raise ValueError('Could not find application root')
  return app_root

def StripParam(url, param, replacement=None):
  urlparts = urlparse.urlsplit(url)
  query = urlparse.parse_qs(urlparts.query)
  logging.debug('Query params: %r', query)
  if replacement:
    query[param] = replacement
  elif param in query:
    del(query[param])
  stripped_url = urlparts._replace(
    query=urllib.urlencode(query, doseq=True))
  logging.debug('Stripped url is: %r', stripped_url)
  return stripped_url.geturl()
