#!/usr/bin/env python
# from datetime import datetime
import hashlib
import json
import logging
# import MySQLdb
import os
# import urllib
import traceback
import webapp2

from webapp2_extras import routes
from google.appengine.ext.webapp import template

from decorator import required_params
from decorator import login_required
from account_utils import get_user_address
from account_utils import get_user_email_address
from account_utils import get_user_id
from account_utils import get_current_username
from blockchain_utils import find_wallet_balance
from global_utils import BaseHandler
from global_utils import init_db
from global_utils import is_development_env

from config import CONFIG




class AccountHomeHandler(BaseHandler):
    @login_required
    def get(self):

        username = get_current_username(self)

        user_id = get_user_id(username)
        email_address = get_user_email_address(user_id)
        ethereum_address = get_user_address(user_id)
        _json_balance = json.loads(find_wallet_balance(ethereum_address))
        hong_balance = _json_balance["balance"] if _json_balance["success"] else 0


        template_values = {
            "ethereum_address": ethereum_address,
            "hong_balance": hong_balance,
            "is_logged_in": (username and username != ""),
            "user_id": user_id,
            "email_address": email_address,
            "username": username,
            "hongcoin_update_status": self.session.get('hongcoin_update_status', ''),
        }
        self.session['hongcoin_update_status'] = ""
        path = os.path.join(os.path.dirname(__file__), 'template/account_home.html')
        self.response.write(template.render(path, template_values))


class AccountEditPasswordHandler(BaseHandler):
    @login_required
    def get(self):

        username = get_current_username(self)

        user_id = get_user_id(username)
        email_address = get_user_email_address(user_id)
        ethereum_address = get_user_address(user_id)
        _json_balance = json.loads(find_wallet_balance(ethereum_address))
        hong_balance = _json_balance["balance"] if _json_balance["success"] else 0


        template_values = {
            "ethereum_address": ethereum_address,
            "hong_balance": hong_balance,
            "is_logged_in": (username and username != ""),
            "user_id": user_id,
            "email_address": email_address,
            "username": username,
            "hongcoin_editpw_error": self.session.get('hongcoin_editpw_error', ''),
        }
        self.session['hongcoin_editpw_error'] = ""
        path = os.path.join(os.path.dirname(__file__), 'template/account_edit_password.html')
        self.response.write(template.render(path, template_values))

    @login_required
    @required_params("current_password", "new_password")
    def post(self):
        current_password = self.request.get("current_password")
        new_password = self.request.get("new_password")

        username = get_current_username(self)
        user_id = get_user_id(username)

        current_password_hash = hashlib.sha512(current_password).hexdigest()

        # verify with password hash
        db = init_db()

        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT * FROM `user` WHERE `id`=%s AND `password_hash`=%s LIMIT 1;",
                (user_id, current_password_hash)
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
        else:
            # password incorrect
            self.session['hongcoin_editpw_error'] = """
                <div class='error_message'>
                    <div class='error_message_inner'>The current password is not correct.</div>
                </div>"""
            self.redirect("/account/password")
            return

        new_password_hash = hashlib.sha512(new_password).hexdigest()

        cursor = db.cursor()
        try:
            cursor.execute(
                "UPDATE `user` SET `password_hash`=%s WHERE `id`=%s;",
                (new_password_hash, user_id)
            )

            db.commit()

        except:
            stacktrace = traceback.format_exc()
            logging.error("db rollback \n\n%s", stacktrace)
            db.rollback()
            self.session['hongcoin_editpw_error'] = """
                <div class='error_message'>
                    <div class='error_message_inner'>Some error occurred. Please try again later.</div>
                </div>"""
            self.redirect("/account/password")
            return

        self.session['hongcoin_update_status'] = """
                <div class='success_message'>
                    <div class='success_message_inner'>Password is changed successfully</div>
                </div>"""
        self.redirect("/account/")


class NotFoundPageHandler(BaseHandler):
    def get(self):
        logging.info("NotFoundPageHandler triggered from " + os.path.basename(__file__))
        self.error(404)
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'template/404.html')
        self.response.write(template.render(path, template_values))



app = webapp2.WSGIApplication([
    routes.PathPrefixRoute('/account', [
        webapp2.Route('/', AccountHomeHandler),
        webapp2.Route('/password', AccountEditPasswordHandler),
    ]),
    ('/.*', NotFoundPageHandler),
], config=CONFIG, debug=is_development_env())

