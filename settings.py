#
# These variables should be overriden with correct values in local_settings.py
#

CONTEXT = 'the-deployment-context'
SECRET_KEY = 'The secret key you need to override in local_settings.py'
LOGIN_URL = 'http://your-sso-login-form.replaceme'
JIRA_URL = 'https://your-jira-instance.replaceme'
SB_URL = 'https://your-sb-url.replaceme/the-deployment-content'
CROWD_CONF = ('URL', 'USER', 'PW')
LOGFILE = 'suggestions.log'

# this user must have write rights in the SuggestionBox project
USER = ('user-with-write-rights', 'a-passwd')

# user for anonymous access to suggestion box
RO_USER = ('user-with-read-only-rights', 'annother-passwd')

# Thou shalt define yer constants in that file
from local_settings import *

FEED_URL = 'https://{}:{}@{}/activity?maxResults=20&streams=key+IS+SB&issues=activity+IS+comment:post+file:post+issue:post+issue:transition&os_authType=basic'.format(*RO_USER, JIRA_URL)
