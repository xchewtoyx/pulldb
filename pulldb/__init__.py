import os
import site

from pulldb.util import AppRoot

site.addsitedir(os.path.join(AppRoot(), 'site-packages'))

