import os
import site
import sys

approot = os.path.dirname(__file__)
sys.path.append(os.path.join(approot, 'lib'))
site.addsitedir(os.path.join(approot, 'site-packages'))
