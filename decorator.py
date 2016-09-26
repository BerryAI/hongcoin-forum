
import json
import logging
import os
import urllib
from account_utils import get_current_username


def log_required_params(*ar):
    """
    Use of Decorator
    http://www.artima.com/weblogs/viewpost.jsp?thread=240845
    """
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            self = args[0]
            error_count = 0

            for param in ar:
                if not self.request.get(param):
                    logging.debug("Error: Parameter \"" + param + "\" does not exist in the request")
                    error_count = error_count + 1

                else:
                    logging.debug(param + ' = \"' + self.request.get(param) + '\"')

            if error_count > 0:
                logging.debug('Missing required parameters. Error message returned')
                self.response.status = 400
                self.response.headers["Content-Type"] = "application/json"
                self.response.write(json.dumps({"success": False, "message": "PARAMETER_MISSING"}))
                return

            f(*args, **kwargs)

        return wrapped_f
    return wrap
#

def required_params(*ar):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            self = args[0]
            error_count = 0

            for param in ar:
                if not self.request.get(param):
                    logging.debug("Error: Parameter \"" + param + "\" does not exist in the request")
                    error_count = error_count + 1

            if error_count > 0:
                logging.debug('Missing required parameters. Error message returned')
                self.response.status = 400
                self.response.headers["Content-Type"] = "application/json"
                self.response.write(json.dumps({"success": False, "message": "PARAMETER_MISSING"}))
                return

            f(*args, **kwargs)

        return wrapped_f
    return wrap
#


def log_optional_params(*ar):

    def wrap(f):
        def wrapped_f(*args, **kwargs):
            self = args[0]

            for param in ar:
                if not self.request.get(param):
                    logging.debug("Parameter \"" + param + "\" does not exist in the request")

                else:
                    logging.debug(param + ' = \"' + self.request.get(param) + '\"')

            f(*args, **kwargs)

        return wrapped_f
    return wrap
#


def login_required(handler):
    """
        Decorator that checks if there's a user associated with the current session.
        Will also fail if there's no session present.
    """
    def check_login(self, *args, **kwargs):
        current_username = get_current_username(self)

        if current_username and current_username != "":
            return handler(self, *args, **kwargs)
        else:
            self.redirect("/signin?continue=" + urllib.quote_plus(os.environ["PATH_INFO"] + "?" + os.environ["QUERY_STRING"]))
            return

    return check_login

