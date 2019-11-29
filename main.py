import hashlib
import random, uuid
from flask import Flask, render_template, request, make_response, url_for, redirect

from models import User, db

app = Flask(__name__)
db.create_all()


@app.route("/", methods=["GET"])
def index():
    session_token = request.cookies.get("session_token")
    if session_token:
        user = db.query(User).filter_by(session_token=session_token).first()
    else:
        user = None

    return render_template("index2.html", user=user)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")
    email = request.form.get("user-email")
    password = request.form.get("user-password")
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    secret_number = random.randint(1, 30)
    user = db.query(User).filter_by(email=email).first()
    # user = User.fetch_one(query=["email", "==", email])
    if not user:
        user = User(name=name, email=email, secret_number=secret_number, password=hashed_password)
        db.add(user)
        db.commit()
    if hashed_password != user.password:
        return "WRONG PASSWORD! Go back and try again"
    elif hashed_password == user.password:
        # generate random session number
        session_token = str(uuid.uuid4())
        user.session_token = session_token
        db.add(user)
        db.commit()

        response = make_response(redirect(url_for('index')))
        response.set_cookie("session_token", session_token, httponly=True, samesite='Strict')
        return response


@app.route("/result", methods=["POST"])
def result():
    guess = int(request.form.get("guess"))

    session_token = request.cookies.get("session_token")
    user = db.query(User).filter_by(session_token=session_token).first()
    if guess == user.secret_number:
        message = "You guessed the secret number! The secret number is {0}".format(str(user.secret_number)) + "."
        new_secret = random.randint(1, 30)  # neue Zufallszahl erstellen
        user.secret_number = new_secret  # dem User Objekt zuordnen
        db.add(user)
        db.commit()

    elif guess > user.secret_number:
        message = "Your guess is wrong..the secret number is smaller."
    elif guess < user.secret_number:
        message = "Your guess is wrong..the secret number is bigger."
    return render_template("result.html", message=message)


@app.route("/profile", methods=["GET"])
def profile():
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token).first()

    if user:
        return render_template("profile.html", user=user)
    else:
        return redirect(url_for("index"))


@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    session_token = request.cookies.get("session_token")

    # get user from the database based on her/his email address
    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "GET":
        if user:  # if user is found
            return render_template("profile_edit.html", user=user)
        else:
            return redirect(url_for("index"))
    elif request.method == "POST":
        name = request.form.get("profile-name")
        email = request.form.get("profile-email")

        # update the user object
        user.name = name
        user.email = email

        # store changes into the database
        db.add(user)
        db.commit()

    return redirect(url_for("profile"))


@app.route("/profile/delete", methods=["GET", "POST"])
def profile_delete():
    session_token = request.cookies.get("session_token")

    # get user from the database based on her/his email address
    user = db.query(User).filter_by(session_token=session_token).first()

    if request.method == "GET":
        if user:  # if user is found
            return render_template("profile_delete.html", user=user)
        else:
            return redirect(url_for("index"))
    elif request.method == "POST":
        # delete the user in the database
        db.delete(user)
        db.commit()

        return redirect(url_for("index"))


@app.route("/users", methods=["GET"])
def all_users():
    users = db.query(User).all()

    return render_template("users.html", users=users)


if __name__ == '__main__':
    app.run(debug=True)
