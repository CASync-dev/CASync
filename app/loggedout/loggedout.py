from flask import Blueprint, flash, render_template, redirect, request, url_for
from flask_login import current_user, login_user

from app.form import LoginForm, RegisterForm
from app.models import User
from app import db

loggedout = Blueprint('loggedout', __name__, template_folder='../templates/loggedout', static_folder='../static')

@loggedout.route("/")
@loggedout.route("/index")
def index():
    return render_template('loggedout/homepage.html')

@loggedout.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.verify_password(form.password.data):
            login_user(user)
            return redirect(url_for('loggedin.dash'))
        else:
            flash('Invalid username or password', 'error')
    return render_template("loggedout/login.html", form=form)


@loggedout.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    form=RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'error')
            return render_template("loggedout/register.html", form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', 'error')
            return render_template("loggedout/register.html", form=form)
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.password = form.password.data
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful.', 'success')
        login_user(new_user)
        return redirect(url_for('loggedin.dash'))
    return render_template("loggedout/register.html", form=form)

# Added /home as a redirect to index, otherwise you can access the homepage from both routes and it's kinda odd
@loggedout.route("/home")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    return redirect(url_for('loggedout.index'))

@loggedout.route("/faq")
def faq():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    return render_template("loggedout/faq.html")

@loggedout.route("/contactus")
def contactus():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    return render_template("loggedout/contact-us.html")

# Added a logout route that logs the user out and redirects to the homepage
from flask_login import logout_user
@loggedout.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('loggedout.login'))