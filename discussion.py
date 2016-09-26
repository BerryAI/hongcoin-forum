#!/usr/bin/env python
# from datetime import datetime
import logging
import MySQLdb
import os
import urllib
import json
import traceback
import webapp2

from webapp2_extras import routes
from google.appengine.ext.webapp import template

# from decorator import required_params
from decorator import login_required
# from global_utils import init_db
from account_utils import get_user_address
from account_utils import get_user_id
from account_utils import get_current_username
from blockchain_utils import find_wallet_balance
from forum_utils import find_category_by_slug
from forum_utils import find_thread
from forum_utils import query_posts
from global_utils import BaseHandler
from global_utils import init_db
from global_utils import is_development_env
from global_utils import is_staging_env

from config import CONFIG




class DiscussionHomeHandler(BaseHandler):
    def get(self):

        username = get_current_username(self)
        if username:
            user_id = get_user_id(username)
            ethereum_address = get_user_address(user_id)
            _json_balance = json.loads(find_wallet_balance(ethereum_address))
            hong_balance = _json_balance["balance"] if _json_balance["success"] else 0

        else:
            user_id = 0
            ethereum_address = ""
            hong_balance = 0

        # forum data

        db = init_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute("""
SELECT cat_info.*, post_info.*, u.username FROM (
    SELECT a.*, b.* FROM (
        SELECT c.id AS cat_id, c.*, COUNT(DISTINCT t.id) threads, COUNT(p.id) posts
        FROM category c
        LEFT JOIN thread t
            ON t.category_id=c.id
        LEFT JOIN post p
            ON p.thread_id=t.id

        GROUP BY c.id
        ORDER BY c.`rank`) a

    LEFT JOIN (
        SELECT category_id AS thread_category_id, max(max_datetime) AS max_categorypost_datetime
        FROM (
            SELECT *
            FROM (
                SELECT thread_id AS post_thread_id, max(datetime) AS max_datetime
                FROM post
                GROUP BY thread_id
            ) y
            JOIN thread t
            ON t.id = y.post_thread_id) a
            GROUP BY category_id
        ) b
        ON a.id = b.thread_category_id

    ORDER BY a.cat_id
) cat_info
LEFT JOIN (

    SELECT a.*, x.title, x.category_id
    FROM (
        SELECT y.*, z.*
        FROM (
            SELECT thread_id AS post_thread_id, max(datetime) AS max_datetime
            FROM post
            GROUP BY thread_id
        ) y
        LEFT JOIN post z
            ON y.max_datetime = z.datetime
            AND z.thread_id = y.post_thread_id) a
        LEFT JOIN thread x
        ON a.post_thread_id = x.id

    ) post_info
    ON cat_info.max_categorypost_datetime = post_info.datetime
    AND cat_info.cat_id = post_info.category_id
LEFT JOIN user u
    ON u.id = post_info.author_id
;
""")

        except:
            stacktrace = traceback.format_exc()
            logging.error("db rollback \n\n%s", stacktrace)
            self.response.write("error")
            return

        forum_category_result = []
        for r in cursor.fetchall():
            max_datetime = r["max_categorypost_datetime"]
            if r["max_categorypost_datetime"]:
                datetime_short_formatted = max_datetime.strftime("%b %d, %Y")
            else:
                datetime_short_formatted = ""

            forum_category_result.append({
                "id": r["id"],
                "name": r["name"],
                "slug": r["category_slug"],
                "desc": r["description"],
                "rank": r["rank"],
                "is_public": r["is_public"],
                "fa_icon": r["fa_icon"],
                "icon_color": r["icon_color"],
                "thread_count": r["threads"],
                "post_count": r["posts"],
                "max_datetime": r["max_categorypost_datetime"],
                "datetime_short_formatted": datetime_short_formatted,
                "author_id": r["author_id"],
                "username": r["username"],
                "latest_post_title": r["title"],
            })

        template_values = {
            "ethereum_address": ethereum_address,
            "hong_balance": hong_balance,
            "signin_path": "/signin?continue=" + urllib.quote_plus(os.environ["PATH_INFO"] + "?" + os.environ["QUERY_STRING"]),
            "is_logged_in": (username and username != ""),
            "username": username,
            "forum_category_result": forum_category_result,
            "is_development_env": is_development_env(),
            "is_staging_env": is_staging_env(),
        }
        path = os.path.join(os.path.dirname(__file__), 'template/discussion_home.html')
        self.response.write(template.render(path, template_values))



class DiscussionThreadsHandler(BaseHandler):
    def get(self, category_slug):

        username = get_current_username(self)
        if username:
            user_id = get_user_id(username)
            ethereum_address = get_user_address(user_id)
            _json_balance = json.loads(find_wallet_balance(ethereum_address))
            hong_balance = _json_balance["balance"] if _json_balance["success"] else 0

        else:
            user_id = 0
            ethereum_address = ""
            hong_balance = 0

        category = find_category_by_slug(category_slug)
        if not category:
            logging.info("Category " + category_slug + " was not found")
            self.response.write("Category does not exist")
            return
        logging.info("id of %s = %s", category_slug, category["id"])


        # forum data

        db = init_db()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        try:

            cursor.execute("""
SELECT   t.*, c.*, x.id AS post_id, x.author_id AS post_author_id, x.datetime AS post_datetime, user.username
FROM     thread t
    JOIN     (
        SELECT      p.*
        FROM        post p
        INNER JOIN  (
                SELECT   thread_id, MAX(datetime) AS MaxDateTime
                FROM     post
                GROUP BY thread_id
            ) pp
            ON      p.thread_id = pp.thread_id
            AND     p.datetime = pp.MaxDateTime
        ) x
    ON t.id = x.thread_id
JOIN (SELECT COUNT(DISTINCT(id)) AS post_count, thread_id FROM post GROUP BY thread_id) c
    ON c.thread_id = t.id
JOIN user
    ON user.id = x.author_id
WHERE    t.is_hidden IS FALSE
    AND  t.category_id = %s

ORDER BY t.is_pinned DESC, x.datetime DESC;

""", (category["id"],))

        except:
            stacktrace = traceback.format_exc()
            logging.error("db rollback \n\n%s", stacktrace)
            self.response.write("error")
            return

        forum_thread_result = []
        for r in cursor.fetchall():
            forum_thread_result.append({
                "id": r["id"],
                "title": r["title"],
                "thread_author_id": r["author_id"],
                "category_id": r["category_id"],
                "datetime": r["datetime"],
                "is_pinned": r["is_pinned"],
                "is_reported": r["is_reported"],
                "is_closed": r["is_closed"],
                "post_count": r["post_count"],
                "username": r["username"],
                "post_datetime": r["post_datetime"],
                "post_datetime_formatted": r["post_datetime"].strftime("%I:%M %p, %b %d"),
            })

        template_values = {
            "ethereum_address": ethereum_address,
            "hong_balance": hong_balance,
            "signin_path": "/signin?continue=" + urllib.quote_plus(os.environ["PATH_INFO"] + "?" + os.environ["QUERY_STRING"]),
            "is_logged_in": (username and username != ""),
            "username": username,
            "category": category,
            "forum_thread_result": forum_thread_result,
            "is_development_env": is_development_env(),
            "is_staging_env": is_staging_env(),
        }
        path = os.path.join(os.path.dirname(__file__), 'template/discussion_thread_list.html')
        self.response.write(template.render(path, template_values))



class CreateNewThreadHandler(BaseHandler):
    @login_required
    def get(self, category_slug):

        username = get_current_username(self)
        if username:
            user_id = get_user_id(username)
            ethereum_address = get_user_address(user_id)
            _json_balance = json.loads(find_wallet_balance(ethereum_address))
            hong_balance = _json_balance["balance"] if _json_balance["success"] else 0

        else:
            user_id = 0
            ethereum_address = ""
            hong_balance = 0

        category = find_category_by_slug(category_slug)
        if not category:
            logging.info("Category " + category_slug + " was not found")
            self.response.write("Category does not exist")
            return
        logging.info("id of %s = %s", category_slug, category["id"])

        template_values = {
            "ethereum_address": ethereum_address,
            "hong_balance": hong_balance,
            "is_logged_in": (username and username != ""),
            "username": username,
            "category": category,
            "is_development_env": is_development_env(),
            "is_staging_env": is_staging_env(),
        }

        path = os.path.join(os.path.dirname(__file__), 'template/discussion_create_thread.html')
        self.response.write(template.render(path, template_values))



class DiscussionPostsHandler(BaseHandler):
    def get(self, category_slug, thread_id):

        username = get_current_username(self)
        if username:
            user_id = get_user_id(username)
            ethereum_address = get_user_address(user_id)
            _json_balance = json.loads(find_wallet_balance(ethereum_address))
            hong_balance = _json_balance["balance"] if _json_balance["success"] else 0

        else:
            user_id = 0
            ethereum_address = ""
            hong_balance = 0

        category = find_category_by_slug(category_slug)
        if not category:
            logging.info("Category %s was not found" % category_slug)
            self.response.write("Category does not exist")
            return
        logging.info("id of %s = %s", category_slug, category["id"])

        thread = find_thread(thread_id)
        if not thread:
            logging.info("Thread %s was not found" % thread_id)
            self.response.write("Topic does not exist")
            return

        posts = query_posts(thread_id)
        if len(posts) == 0:
            logging.info("Posts was not found under thread %s" % thread_id)
            self.response.write("Posts was not found")
            return

        template_values = {
            "ethereum_address": ethereum_address,
            "hong_balance": hong_balance,
            "signin_path": "/signin?continue=" + urllib.quote_plus(os.environ["PATH_INFO"] + "?" + os.environ["QUERY_STRING"]),
            "is_logged_in": (username and username != ""),
            "username": username,
            "category": category,
            "thread": thread,
            "posts": posts,
            "is_development_env": is_development_env(),
            "is_staging_env": is_staging_env(),
        }
        path = os.path.join(os.path.dirname(__file__), 'template/discussion_thread_post.html')
        self.response.write(template.render(path, template_values))



class NotFoundPageHandler(BaseHandler):
    def get(self):
        logging.info("NotFoundPageHandler triggered from " + os.path.basename(__file__))
        self.error(404)
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'template/404.html')
        self.response.write(template.render(path, template_values))



app = webapp2.WSGIApplication([
    webapp2.Route('/', DiscussionHomeHandler),
    routes.PathPrefixRoute('/discussion', [
        webapp2.Route('/', DiscussionHomeHandler),
        webapp2.Route('/<category_slug:.+>/', DiscussionThreadsHandler),
        webapp2.Route('/<category_slug:.+>/new', CreateNewThreadHandler),
        webapp2.Route('/<category_slug:.+>/<thread_id:\d+>', DiscussionPostsHandler),
    ]),
    ('/.*', NotFoundPageHandler),
], config=CONFIG, debug=is_development_env())

