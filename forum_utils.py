#!/usr/bin/env python
# import logging
# import os
import MySQLdb
import markdown2

from global_utils import init_db

#deprecated
# def find_latest_post_detail_by_category(category_id):

#     db = init_db()
#     cursor = db.cursor(MySQLdb.cursors.DictCursor)
#     cursor.execute("""
# SELECT  a.*, b.*, u.username
# FROM    (SELECT * FROM thread WHERE category_id = %s) a
# JOIN    (SELECT DISTINCT(thread_id), max(datetime) AS dt FROM post GROUP BY thread_id ORDER BY MAX(datetime) DESC, thread_id ) b
#     ON  a.id = b.thread_id
# JOIN    post p
#     ON  p.datetime = b.dt
# JOIN    user u
#     ON u.id = p.author_id
# ;
# """, (category_id,))

#     data = cursor.fetchone()
#     if data:
#         data["datetime_short_formatted"] = data["dt"].strftime("%b %d, %Y")
#         return data
#     else:
#         return None


def find_category_id(category_slug):

    db = init_db()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT id FROM `category` WHERE category_slug = %s
    """, (category_slug,))

    data = cursor.fetchone()
    if data:
        return data["id"]
    else:
        return 0


def find_category_by_slug(category_slug):

    db = init_db()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT * FROM `category` WHERE category_slug = %s
    """, (category_slug,))

    return cursor.fetchone()


def find_thread(thread_id):

    db = init_db()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT * FROM `thread` WHERE id = %s
    """, (thread_id,))

    return cursor.fetchone()


def query_posts(thread_id):

    db = init_db()
    cursor = db.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
SELECT post.*, user.username FROM `post`
JOIN user ON user.id = post.author_id
WHERE thread_id = %s ORDER BY post.`datetime`;
""", (thread_id,))


    post_result = []
    for r in cursor.fetchall():
        post_result.append({
            "id": r["id"],
            "datetime": r["datetime"],
            "datetime_formatted": r["datetime"].strftime("%I:%M %p, %b %d, %Y"),
            "author_id": r["author_id"],
            "author_username": r["username"],
            "content": r["content"],
            "content_html": markdown2.markdown(r["content"], extras=["fenced-code-blocks"]),
        })
    return post_result




