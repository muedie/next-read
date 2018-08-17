import os

from flask import Flask, flash, session, render_template, jsonify, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, get_goodreads_reviews

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

if not os.getenv("API_KEY"):
    raise RuntimeError("API_KEY is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Main page where user can search and click the book for more info"""

    if request.method == "POST":
        # post request for search

        query = request.form.get("query")

        # ensure there's search text
        if not query:
            flash("Empty Search String!")
            return redirect("/")

        # search for books
        books = []

        # look by isbn
        rows = db.execute(
            "SELECT * FROM books WHERE LOWER(books.isbn) LIKE :query", {"query": '%' + query.lower() + '%'})

        # return out if query matches any isbn
        if rows.rowcount > 0:
            books.extend(rows.fetchall())
            return render_template("index.html", books=books, query=query)

        # look by title
        rows = db.execute(
            "SELECT * FROM books WHERE LOWER(books.title) LIKE :query", {"query": '%' + query.lower() + '%'})

        books.extend(rows.fetchall())

        # look by author
        rows = db.execute(
            "SELECT * FROM books WHERE LOWER(books.author) LIKE :query", {"query": '%' + query.lower() + '%'})

        books.extend(rows.fetchall())

        if len(books) < 1:
            flash("No results found!")

        print("QUERY: ", query)

        return render_template("index.html", books=books, query=query)

    else:
        # get request
        return render_template("index.html")


@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):

    if request.method == "POST":

        # grab info from form
        rating = request.form.get("rating")
        review = request.form.get("review")

        if not rating or int(rating) < 1 or int(rating) > 5:
            flash("Review Failed, Invalid Rating!")
        elif not review:
            flash("Review Failed, Plese enter some text!")
        else:
            # we have rating & review

            # check if user already left review
            rows = db.execute("SELECT * from reviews WHERE book_isbn = :isbn AND user_id = :uid", {
                              "isbn": isbn, "uid": session["user_id"]})

            if rows.rowcount > 0:
                flash("Review Failed, Already left a review!")
            else:
                # able to post review
                db.execute('INSERT INTO reviews ("user_id", "review", "rating", "book_isbn") VALUES (:uid, :review, :rating, :isbn)', {
                    "uid": session["user_id"],
                    "review": review,
                    "rating": rating,
                    "isbn": isbn
                })

                db.commit()

        # grab book info
        rows = db.execute(
            "SELECT * FROM books WHERE books.isbn = :isbn", {"isbn": isbn})

        book = rows.fetchone()

        # get reviews
        rows = db.execute(
            "SELECT reviews.*, users.username FROM reviews INNER JOIN users ON reviews.user_id = users.id WHERE book_isbn = :isbn", {"isbn": isbn})

        reviews = rows.fetchall()

        star_string = dict()

        for i in range(len(reviews)):

            rating_string = ''

            for j in range(5):
                if j < reviews[i][3]:
                    rating_string += '\u2605 '
                else:
                    rating_string += '\u2606 '

            star_string[reviews[i][0]] = rating_string

        return render_template("book.html", book=book, reviews=reviews, star_string=star_string)
    else:

        # GET request: grab book info
        rows = db.execute(
            "SELECT * FROM books WHERE books.isbn = :isbn", {"isbn": isbn})

        book = rows.fetchone()

        # get reviews
        rows = db.execute(
            "SELECT reviews.*, users.username FROM reviews INNER JOIN users ON reviews.user_id = users.id WHERE book_isbn = :isbn", {"isbn": isbn})

        reviews = rows.fetchall()

        star_string = dict()

        for i in range(len(reviews)):

            rating_string = ''

            for j in range(5):
                if j < reviews[i][3]:
                    rating_string += '\u2605 '
                else:
                    rating_string += '\u2606 '

            star_string[reviews[i][0]] = rating_string

        return render_template("book.html", book=book, reviews=reviews, star_string=star_string)


@app.route("/api/<string:isbn>")
def book_info(isbn):
    """ API route for info about book for given ISBN  # """

    stats = get_goodreads_reviews(isbn)

    return jsonify({
        "isbn": isbn,
        **stats
    })


@app.route("/login", methods=["GET", "POST"])
def login():
    """User Log-in Page"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == 'POST':

        # Ensure form was filled
        if not request.form.get('username'):
            flash("Must provide Username!")
            return render_template("login.html")
        elif not request.form.get('password'):
            flash("Password not provided!")
            return render_template("login.html")

        # Query database for username
        rows = db.execute(
            'SELECT * FROM users WHERE username = :username',
            {"username": request.form.get('username')})

        # grab the user from proxy
        user = rows.fetchone()

        # Ensure username exists and password is correct
        if rows.rowcount != 1 or not check_password_hash(
                user[2], request.form.get('password')):
            flash("Invalid username and/or password!")
            return render_template("login.html")

        # Remember which user has logged in
        session['user_id'] = user[0]

        # Redirect user to home page
        flash("Successfully Logged in!")
        return redirect('/')

    else:

        # User reached route via GET (as by clicking a link or via redirect)
        return render_template('login.html')


@app.route("/logout")
def logout():
    """Log user out"""

    # clear session var
    session.clear()

    # redirect user
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == 'POST':

        # Ensure username was submitted
        if not request.form.get('username'):
            flash("Must provide username!")
            return render_template("register.html")
        elif not request.form.get('password') or not request.form.get(
                'confirmation'):
            # Ensure password was submitted
            flash("Must provide both password!")
            return render_template("register.html")
        elif request.form.get('password') != request.form.get('confirmation'):
            flash("Passwords don't match!")
            return render_template("register.html")

        # Query database for username
        rows = db.execute('SELECT * FROM users WHERE username = :username',
                          {"username": request.form.get('username')})

        # Ensure unique username
        if rows.rowcount > 0:
            flash("Username already exists!")
            return render_template("register.html")

        # add user to db
        rows = db.execute('INSERT INTO users ("username","hash") VALUES (:username,:p_hash)', {
                          "username": request.form.get('username'), "p_hash": generate_password_hash(request.form.get('password'))})
        db.commit()

        # call db again for it? TODO: maybe don't need to do this
        rows = db.execute('SELECT id FROM users WHERE username = :username', {
                          "username": request.form.get('username')})

        # Remember which user has logged in
        session['user_id'] = rows.first()[0]

        # flash registered msg
        flash('Registered!')

        # Redirect user to home page
        return redirect('/')

    else:
        # a GET request, ie show register page
        return render_template("register.html")
