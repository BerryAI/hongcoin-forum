#!/usr/bin/env python
# import logging
import MySQLdb
import os
import webapp2
from webapp2_extras import sessions

from config import _db_config
from config import DEV_APP_ID


def init_db():
    if not is_development_env():
        # Connecting from App Engine
        db = MySQLdb.connect(
            db=_db_config["database"],
            unix_socket=_db_config["unix_socket"],
            user=_db_config["unix_user"],
            passwd=_db_config["unix_password"])

    else:
        # Connecting from an external network.
        # Make sure your network is whitelisted
        db = MySQLdb.connect(
            db=_db_config["database"],
            host=_db_config["host"],
            port=_db_config["port"],
            user=_db_config["user"],
            passwd=_db_config["password"]
        )

    return db


def is_development_env():
    env = os.getenv('SERVER_SOFTWARE')
    if (env and env.startswith('Google App Engine/')):
        return False
    else:
        return True

def is_staging_env():
    if os.environ["APPLICATION_ID"] == DEV_APP_ID:
        return True
    else:
        return False


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

