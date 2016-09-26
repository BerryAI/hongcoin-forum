#!/usr/bin/env python
import json
import logging
from google.appengine.api import urlfetch

from config import API_SERVER_HOSTNAME


def find_wallet_balance(address):
    if address == "":
        return json.dumps({"success": False, "message": "MISSING_PARAMETER"})

    if len(address) != 42:
        return json.dumps({"success": False, "message": "INVALID_ADDRESS"})

    url = "http://" + API_SERVER_HOSTNAME + "/api/balanceOf?address=" + address
    logging.info("url => " + url)

    try:
        urlfetch.set_default_fetch_deadline(10)
        response = urlfetch.fetch(
            url=url,
            method=urlfetch.GET,
            headers={'Accept': 'application/json'}
        )

        return response.content

    except:
        logging.warning("urlfetch failure")
        return json.dumps({"success": False, "message": "SERVER_ERROR"})
    #

