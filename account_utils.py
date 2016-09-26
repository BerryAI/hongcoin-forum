#!/usr/bin/env python
import logging
import os
import urllib
import json
# import webapp2

from google.appengine.api import urlfetch
from config import RECAPTCHA_SECRET
from config import RECAPTCHA_VERIFY_HOST
from global_utils import init_db



def do_login(self, username):

    # To set a value:
    self.session['hongcoin_username'] = username

    return True

def do_logout(self):

    # To set a value:
    self.session.pop('hongcoin_username')

    return True


def get_current_username(self):
    return self.session.get('hongcoin_username')


def get_user_id(username):
    db = init_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM `user` WHERE username = %s', (username,))

    data = cursor.fetchone()
    if data and data[0] > 0:
        return data[0]
    else:
        return 0


def get_user_address(user_id):
    # TODO
    #   This function only returns the first address entered by the user.
    #   If he has more than one ethereum wallet addresses, we do not support this yet.
    db = init_db()
    cursor = db.cursor()
    cursor.execute('SELECT wallet_address FROM `user_address` WHERE user_id = %s', (user_id,))

    data = cursor.fetchone()
    if data:
        return data[0]
    else:
        return ""


def get_user_email_address(user_id):
    db = init_db()
    cursor = db.cursor()
    cursor.execute('SELECT email FROM `user` WHERE id = %s', (user_id,))

    data = cursor.fetchone()
    if data:
        return data[0]
    else:
        return ""


def validate_recaptcha(self):
    self.response.headers["Content-Type"] = "application/json"

    recaptcha_response = self.request.get('g-recaptcha-response', '')

    if recaptcha_response == "":
        return (False, "EMPTY_RECAPTCHA_RESPONSE")


    form_fields = {
        "secret": RECAPTCHA_SECRET,
        "response": recaptcha_response,
        "remoteip": os.environ["REMOTE_ADDR"]
    }
    form_data = urllib.urlencode(form_fields)
    logging.info(form_data)

    # validate google recaptcha form
    try:
        urlfetch.set_default_fetch_deadline(30)
        result = urlfetch.fetch(
            url=RECAPTCHA_VERIFY_HOST,
            payload=form_data,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
    except:
        logging.warning("urlfetch failure")
        return (False, "SERVER_ERROR")
    #

    # parse reCaptcha result from Google
    logging.info(result.content)
    result_json = json.loads(result.content)

    if result_json["success"] is False:

        logging.info("Captcha is invalid")
        return False, "INVALID_RECAPTCHA_RESPONSE"

    else:
        logging.info("Captcha is valid")
        return True, ""


def validate_unique_wallet_address(address):
    db = init_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM `user_address` WHERE wallet_address = %s', (address,))

    data = cursor.fetchone()
    if data[0] > 0:
        logging.info("Count = " + str(data[0]))
        return False
    else:
        return True


def validate_unique_email_address(email_address):
    db = init_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM `user` WHERE email = %s', (email_address,))

    data = cursor.fetchone()
    if data[0] > 0:
        logging.info("Count = " + str(data[0]))
        return False
    else:
        return True


def validate_unique_username(username):
    db = init_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM `user` WHERE `username` = %s', (username,))

    data = cursor.fetchone()
    if data[0] > 0:
        logging.info("Count = " + str(data[0]))
        return False
    else:
        return True

