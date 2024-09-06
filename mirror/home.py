from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response
import re

from mirror.model import User, Tailor, Courier

home = Blueprint("home", __name__)


@home.route("/", methods=['GET', 'POST'])
def land_page():
    if 'user_id' in session:
        return redirect(url_for("user.home"))
    elif 'tailor_id' in session:
        return redirect(url_for("tailor.home"))
    elif 'courier_id' in session:
        return redirect(url_for("courier.home"))

    return render_template("landing_page.html")


@home.route("/login", methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for("user.home"))
    elif 'tailor_id' in session:
        return redirect(url_for("tailor.home"))
    elif 'courier_id' in session:
        return redirect(url_for("courier.home"))

    if request.method == "POST":
        data = request.form.to_dict(flat = True)
        email = data['Email']
        role = data['Role']

        if role == 'Tailor':
            tailor = Tailor.query.filter_by(email=email).first()
            if not tailor:
                flash("Invalid Email Address")
                return redirect(url_for("home.login"))
            if tailor.password != data['password']:
                flash("Invalid Password")
                return redirect(url_for("home.login"))
            if tailor.password == data['password']:
                tailor.add_to_session()
                return redirect(url_for("tailor.home"))

        elif role == "Customer":
            user = User.query.filter_by(email=email).first()
            if not user:
                flash("Invalid Email Address")
                return redirect(url_for("home.login"))
            if user.password != data['password']:
                flash("Invalid Password")
                return redirect(url_for("home.login"))
            if user.password == data['password']:
                user.add_to_session()
                return redirect(url_for("user.home"))

        elif role == "Courier":
            courier = Courier.query.filter_by(email=email).first()
            if not courier:
                flash("Invalid Email Address")
                return redirect(url_for("home.login"))
            if courier.password != data['password']:
                flash("Invalid Password")
                return redirect(url_for("home.login"))
            if courier.password == data['password']:
                courier.add_to_session()
                return redirect(url_for("courier.home"))

    return render_template("login.html")


@home.route("/register", methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for("user.home"))
    elif 'tailor_id' in session:
        return redirect(url_for("tailor.home"))
    elif 'courier_id' in session:
        return redirect(url_for("courier.home"))

    if request.method == "POST":
        data = request.form.to_dict(flat=True)
        role_name = data['Role']
        email = data['Email']
        password = data['password']

        # Regular expression to validate email
        email_regex = r'^[a-zA-Z0-9]+@gmail\.com$'

        if not re.match(email_regex, email):
            flash("Please enter a valid email address.")
            return redirect(url_for("home.register"))

        # Regular expression to validate password
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$'

        if not re.match(password_regex, password):
            flash("Please set strong password.")
            return redirect(url_for("home.register"))

        if role_name == "Customer":
            if User.query.filter(User.email == email).first():
                flash("Email already exists. Please try with another.")
                return redirect(url_for("home.register"))
        elif role_name == "Tailor":
            if Tailor.query.filter(Tailor.email == email).first():
                flash("Email already exists. Please try with another.")
                return redirect(url_for("home.register"))
        elif role_name == "Courier":
            if Courier.query.filter(Courier.email == email).first():
                flash("Email already exists. Please try with another.")
                return redirect(url_for("home.register"))

        if role_name == "Customer":
            user = User(username=data['u-name'], email=data['Email'], password=data['password'])
            user.save_to_database()
            user.add_to_session()
            return redirect(url_for("user.home"))
        elif role_name == "Tailor":
            tailor = Tailor(username=data['u-name'], email=data['Email'], password=data['password'])
            tailor.save_to_database()
            tailor.add_to_session()
            return redirect(url_for("tailor.home"))
        elif role_name == "Courier":
            courier = Courier(username=data['u-name'], email=data['Email'], password=data['password'])
            courier.save_to_database()
            courier.add_to_session()
            return redirect(url_for("courier.home"))

    return render_template("register.html")


@home.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.land_page"))
