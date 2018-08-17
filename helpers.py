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