import json

import pycomicvine
from pycomicvine import Issue, Issues, Volume
from pycomicvine import error
from pulldb.models.admin import Setting

def load():
    pycomicvine.api_key = Setting.query(
      Setting.name == 'comicvine_api_key').get().value
