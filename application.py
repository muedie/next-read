import os

from flask import Flask, flash, session, render_template, jsonify, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

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


@app.route("/")
@login_required
def index():
    """Main page where user can search and click the book for more info"""

    return render_template("index.html")


@app.route("/api/<int:isbn>")
def book_info(isbn):
    """ API route for info about book for given ISBN  # """

    return jsonify([isbn])


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
