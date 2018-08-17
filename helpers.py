# helper functions for application

import os
from flask import redirect, session
from functools import wraps
import requests
from xml.etree import ElementTree


def login_required(f):
    """Decorates routes to require login"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_goodreads_reviews(isbn):
    """Makes api call to goodreads API to retrive review stats"""

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": os.getenv("API_KEY"), "isbns": isbn})

    if res.status_code == 200:
        book = res.json()["books"][0]
        print(book)

    return {
        "ratings_count": book["work_ratings_count"],
        "average_rating": book["average_rating"]
    }


def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc

    NOT MINE: FROM http://evaisse.com/post/93417709/python-pretty-date-function
    """

    from datetime import datetime
    now = datetime.utcnow()

    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time, datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = int(diff.seconds)
    day_diff = int(diff.days)

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff // 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff // 3600) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff // 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff // 30) + " months ago"
    return str(day_diff // 365) + " years ago"
