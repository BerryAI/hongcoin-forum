#!/usr/bin/env python
# from datetime import datetime
import logging
# import MySQLdb
import os
# import urllib
import json
import hashlib
import traceback
import webapp2

# from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template
from account_utils import do_login
from account_utils import do_logout
from account_utils import validate_recaptcha
from account_utils import validate_unique_wallet_address
from account_utils import validate_unique_email_address
from account_utils import validate_unique_username
from blockchain_utils import find_wallet_balance
from decorator import required_params
from decorator import log_optional_params
from global_utils import BaseHandler
from global_utils import init_db
from global_utils import is_development_env

from config import CONFIG


# class MainHandler(BaseHandler):
#     def get(self):

#         template_values = {}
#         path = os.path.join(os.path.dirname(__file__), 'template/home.html')
#         self.response.write(template.render(path, template_values))



class SignupHandler(BaseHandler):
    def get(self):
        template_values = {
            "error_message": self.session.get('hongcoin_signup_error', ''),
            "form_wallet": self.session.get('hongcoin_signup_wallet', ''),
            "form_email": self.session.get('hongcoin_signup_email', ''),
            "form_username": self.session.get('hongcoin_signup_username', '')
        }
        path = os.path.join(os.path.dirname(__file__), 'template/signup.html')
        self.response.write(template.render(path, template_values))

        # unset form session data
        self.session['hongcoin_signup_error'] = ""
        self.session['hongcoin_signup_wallet'] = ""
        self.session['hongcoin_signup_email'] = ""
        self.session['hongcoin_signup_username'] = ""


    @required_params("ethereum_address", "email_input", "username", "password")
    def post(self):

        captcha_result, captcha_message = validate_recaptcha(self)
        ethereum_address = self.request.get("ethereum_address")
        email_address = self.request.get("email_input")
        username = self.request.get("username")
        password = self.request.get("password")
        cpassword = self.request.get("cpassword")

        if captcha_result:

            # checker function
            _has_error = False
            _json_balance = json.loads(find_wallet_balance(ethereum_address))
            hong_balance = _json_balance["balance"] if _json_balance["success"] else 0

            if hong_balance == 0 and not _json_balance["success"]:
                logging.warning("We cannot validate balance of this address yet. Please try again later.")
                self.session['hongcoin_signup_error'] = "We cannot validate balance of this address yet. Please try again later."
                _has_error = True

            elif hong_balance == 0:
                logging.warning("The address does not hold any Hong Tokens")
                self.session['hongcoin_signup_error'] = "The address does not hold any Hong Tokens"
                _has_error = True

            elif password != cpassword:
                logging.warning("Password does not match")
                self.session['hongcoin_signup_error'] = "Password does not match"
                _has_error = True

            elif not validate_unique_wallet_address(ethereum_address):
                logging.warning("Wallet address has been registered")
                self.session['hongcoin_signup_error'] = "%s %s" % (
                    "Wallet address has been registered. ",
                    "<a href='https://docs.google.com/forms/d/e/"
                    "1FAIpQLSdJFq5pbSAG19cWsOWbGF3vVceT550JAw4kb-V2uwoh7DR5Ag/viewform' target='_blank'>Report an issue</a>")
                _has_error = True

            elif not validate_unique_email_address(email_address):
                logging.warning("Email address has been registered")
                self.session['hongcoin_signup_error'] = "Email address has been registered"
                _has_error = True

            elif not validate_unique_username(username):
                logging.warning("username has been registered")
                self.session['hongcoin_signup_error'] = "Username has been registered"
                _has_error = True

            if _has_error:
                self.session['hongcoin_signup_wallet'] = ethereum_address
                self.session['hongcoin_signup_email'] = email_address
                self.session['hongcoin_signup_username'] = username
                self.redirect("/signup")
                return

            # process registration
            # password hash
            password_hash = hashlib.sha512(password).hexdigest()

            # create user with sql
            db = init_db()

            cursor = db.cursor()
            try:
                cursor.execute(
                    "INSERT INTO `user` (`email`, `username`, `password_hash`, `creation_datetime`) VALUES (%s, %s, %s, NOW());",
                    (email_address, username, password_hash)
                )
                cursor.execute(
                    "INSERT INTO `user_address` (`user_id`, `wallet_address`) VALUES (%s, %s);",
                    (cursor.lastrowid, ethereum_address)
                )

                db.commit()
                # self.response.write("db execution finish")

            except:
                stacktrace = traceback.format_exc()
                logging.error("db rollback \n\n%s", stacktrace)
                db.rollback()
                self.session['hongcoin_signup_error'] = "Some error occurred. Please try again later."
                self.redirect("/signup")
                return

            # set user cookie and session
            do_login(self, username)

            self.redirect("/discussion/")

        else:
            logging.info(captcha_message)
            self.session['hongcoin_signup_error'] = "Please verify you are not a robot."
            self.session['hongcoin_signup_wallet'] = ethereum_address
            self.session['hongcoin_signup_email'] = email_address
            self.session['hongcoin_signup_username'] = username
            self.redirect("/signup")
            return


class SigninHandler(BaseHandler):
    def get(self):
        login_qs = self.request.get("login", "")
        login_status = ""
        if login_qs == "failed":
            login_status = "<div class='error_message'><div class='error_message_inner'>Email address/ password incorrect</div></div>"

        template_values = {
            "continue_path": self.request.get("continue", ""),
            "login_status": login_status
        }
        logging.info(self.request.get("continue"))
        path = os.path.join(os.path.dirname(__file__), 'template/signin.html')
        self.response.write(template.render(path, template_values))

    @required_params("email_input", "password")
    @log_optional_params("continue_path")
    def post(self):
        email_address = self.request.get("email_input")
        password = self.request.get("password")
        continue_path = self.request.get("continue_path", "")

        #sign in with email + password
        password_hash = hashlib.sha512(password).hexdigest()

        # query user record with email

        # verify with password hash
        db = init_db()

        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT * FROM `user` WHERE `email`=%s AND `password_hash`=%s LIMIT 1;",
                (email_address, password_hash)
            )
        except:
            stacktrace = traceback.format_exc()
            logging.error("db rollback \n\n%s", stacktrace)
            self.response.write("error")
            return

        data = cursor.fetchone()
        if data:
            # user_id = data[0]
            username = data[2]

            do_login(self, username)

            if(continue_path != ""):
                self.redirect(continue_path)
            else:
                self.redirect("/discussion/")

        else:
            # no record is found
            self.redirect("/signin?login=failed")





class LogoutHandler(BaseHandler):
    def get(self):
        do_logout(self)
        self.redirect("/")





class LetsEncryptHandler(webapp2.RequestHandler):

    def get(self, challenge):
        self.response.headers['Content-Type'] = 'text/plain'
        responses = {
            'xgbGQbB4WMrHv9W4otMF9raEcOrMZKnzV1nTbLEz0T8':
                'xgbGQbB4WMrHv9W4otMF9raEcOrMZKnzV1nTbLEz0T8.RsigBj-ozOspGpgMnUBw2IA5cIM3br3oVEkTd5I20CA'
        }
        self.response.write(responses.get(challenge, ''))


class NotFoundPageHandler(BaseHandler):
    def get(self):
        logging.info("NotFoundPageHandler triggered from " + os.path.basename(__file__))
        self.error(404)
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'template/404.html')
        self.response.write(template.render(path, template_values))



app = webapp2.WSGIApplication([
    # ('/', MainHandler),
    ('/signup', SignupHandler),
    ('/signin', SigninHandler),
    ('/logout', LogoutHandler),

    ('/.well-known/acme-challenge/([\w-]+)', LetsEncryptHandler),
    ('/.*', NotFoundPageHandler),
], config=CONFIG, debug=is_development_env())

