# Copyright 2013 Russell Heilling

import os
import sys

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
