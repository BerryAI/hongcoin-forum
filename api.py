#!/usr/bin/env python
import logging
from webapp2_extras import routes
# import os
# import urllib
import json
import traceback
import webapp2

# from google.appengine.api import urlfetch
from account_utils import get_user_id
from account_utils import get_current_username
from account_utils import validate_unique_wallet_address
from blockchain_utils import find_wallet_balance
from decorator import login_required
from decorator import required_params
from forum_utils import find_category_id
from forum_utils import find_thread
from global_utils import init_db
from global_utils import BaseHandler

from config import CONFIG


class GetAddressTokenBalance(webapp2.RequestHandler):

    def get(self):
        self.response.headers["Content-Type"] = "application/json"
        address = self.request.get("address", "")
        if address == "":
            self.response.write(json.dumps({"success": False, "message": "MISSING_PARAMETER"}))
            return

        if len(address) != 42:
            self.response.write(json.dumps({"success": False, "message": "INVALID_ADDRESS"}))
            return

        self.response.write(find_wallet_balance(address))



class IsAddressHoldingTokenHandler(webapp2.RequestHandler):

    def get(self):
        self.response.headers["Content-Type"] = "application/json"
        address = self.request.get("address", "")
        if address == "":
            self.response.write(json.dumps({"success": False, "message": "MISSING_PARAMETER"}))
            return

        if len(address) != 42:
            self.response.write(json.dumps({"success": False, "message": "INVALID_ADDRESS"}))
            return

        balance = find_wallet_balance(address)
        json_balance = json.loads(balance)

        if json_balance["success"]:
            self.response.write(json.dumps({"success": True, "isHoldingBalance": (json_balance["balance"] > 0)}))
        else:
            self.response.write(json.dumps({"success": False, "message": "INVALID_ADDRESS"}))
        return
        #


class IsAddressRegisteredHandler(webapp2.RequestHandler):

    def get(self):
        self.response.headers["Content-Type"] = "application/json"
        address = self.request.get("address", "")
        if address == "":
            self.response.write(json.dumps({"success": False, "message": "MISSING_PARAMETER"}))
            return

        if len(address) != 42:
            self.response.write(json.dumps({"success": False, "message": "INVALID_ADDRESS"}))
            return

        if validate_unique_wallet_address(address):
            self.response.write(json.dumps({"success": True, "message": ""}))
            return
        else:
            self.response.write(json.dumps({"success": False, "message": "WALLET_REGISTERED"}))
            return
        #



class NewPostToThreadHandler(BaseHandler):
    @login_required
    @required_params("content")
    def post(self, category_slug, thread_id):

        username = get_current_username(self)
        user_id = get_user_id(username)

        category_id = find_category_id(category_slug)
        if category_id == 0:
            logging.info("Category %s was not found" % category_slug)
            self.response.write("Error: Category does not exist")
            return
        logging.info("id of %s = %s", category_slug, category_id)

        thread = find_thread(thread_id)
        if not thread:
            logging.info("Thread %s was not found" % thread_id)
            self.response.write("Error: Topic does not exist")
            return

        content = self.request.get("content")

        # create new post

        db = init_db()
        cursor = db.cursor()

        try:
            cursor.execute("""
INSERT INTO `post` (`author_id`, `datetime`, `thread_id`, `content`, `is_pinned`, `is_reported`, `is_hidden`)
VALUES (%s, NOW(), %s, %s, False, False, False);""", (user_id, thread_id, content))
            db.commit()

        except:
            stacktrace = traceback.format_exc()
            logging.error("db rollback \n\n%s", stacktrace)
            db.rollback()
            self.response.write("Error: Operation failed")
            return

        self.redirect("/discussion/%s/%s" % (category_slug, thread_id))


class NewThreadHandler(BaseHandler):
    @login_required
    @required_params("content", "title")
    def post(self, category_slug):

        username = get_current_username(self)
        user_id = get_user_id(username)

        category_id = find_category_id(category_slug)
        if category_id == 0:
            logging.info("Category %s was not found" % category_slug)
            self.response.write("Error: Category does not exist")
            return
        logging.info("id of %s = %s", category_slug, category_id)

        title = self.request.get("title")
        content = self.request.get("content")

        # create new post

        db = init_db()
        cursor = db.cursor()

        try:
            cursor.execute("""
INSERT INTO `thread` (`title`, `author_id`, `category_id`, `datetime`, `is_pinned`, `is_reported`, `is_closed`, `is_hidden`)
VALUES (%s, %s, %s, NOW(), False, False, False, False);""", (title, user_id, category_id))

            thread_id = cursor.lastrowid

            cursor.execute("""
INSERT INTO `post` (`author_id`, `datetime`, `thread_id`, `content`, `is_pinned`, `is_reported`, `is_hidden`)
VALUES (%s, NOW(), %s, %s, False, False, False);""", (user_id, thread_id, content))
            db.commit()

        except:
            stacktrace = traceback.format_exc()
            logging.error("db rollback \n\n%s", stacktrace)
            db.rollback()
            self.response.write("Error: Operation failed")
            return

        self.redirect("/discussion/%s/%s" % (category_slug, thread_id))


class UpdateEmailHandler(BaseHandler):
    @login_required
    @required_params("email")
    def post(self):

        username = get_current_username(self)
        user_id = get_user_id(username)

        email = self.request.get("email")

        self.response.headers["Content-Type"] = "application/json"

        # create new post

        db = init_db()
        cursor = db.cursor()

        try:
            cursor.execute("""
UPDATE `user` SET `email`=%s WHERE id=%s""", (email, user_id))

            db.commit()

        except:
            stacktrace = traceback.format_exc()
            logging.error("db rollback \n\n%s", stacktrace)
            db.rollback()
            self.response.out.write(json.dumps({"success": False, "message": "SERVER_ERROR"}))
            return

        self.response.out.write(json.dumps({"success": True, "message": ""}))



class NotFoundApiHandler(webapp2.RequestHandler):
    def get(self):
        self.response.status = 404
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(json.dumps({"success": False, "message": "NOT_FOUND"}))

    def post(self):
        self.response.status = 404
        self.response.headers["Content-Type"] = "application/json"
        self.response.out.write(json.dumps({"success": False, "message": "NOT_FOUND"}))




app = webapp2.WSGIApplication([
    routes.PathPrefixRoute('/api', [
        # webapp2.Route('/account/signup', AccountSignupHandler),
        webapp2.Route('/balanceOf', GetAddressTokenBalance),
        webapp2.Route('/isAddressHoldingToken', IsAddressHoldingTokenHandler),
        webapp2.Route('/isAddressRegistered', IsAddressRegisteredHandler),
        webapp2.Route('/discussion/<category_slug:.+>/<thread_id:\d+>', NewPostToThreadHandler),
        webapp2.Route('/discussion/<category_slug:.+>/new', NewThreadHandler),
        webapp2.Route('/account/updateEmail', UpdateEmailHandler),
    ]),
    ('/.*', NotFoundApiHandler),
], config=CONFIG, debug=True)

