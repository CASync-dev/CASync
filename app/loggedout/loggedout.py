from flask import Blueprint, flash, render_template, redirect, request, url_for
from flask_login import current_user, login_user

from app.form import (
    ForgotPasswordForm,
    LoginForm,
    RegisterForm,
    ResetPasswordForm,
    ResendConfirmationForm,
)
from app.models import User
from app import db
from services.email import send_confirmation_email, send_password_reset_email
from services.tokens import load_confirm_token, load_reset_token

loggedout = Blueprint('loggedout', __name__, template_folder='../templates/loggedout', static_folder='../static')

@loggedout.route("/")
def root():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    return redirect(url_for('loggedout.index'))
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
        if not user or not user.verify_password(form.password.data):
            flash('Invalid username or password', 'error')
        elif not user.email_confirmed:
            # Block login until the address is confirmed. The login page carries a
            # link to /resend_confirmation for users who need a fresh link.
            flash('Please confirm your email address before logging in.', 'error')
        else:
            login_user(user)
            return redirect(url_for('loggedin.dash'))
    return render_template("loggedout/login.html", form=form)


@loggedout.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    form=RegisterForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.password = form.password.data
        db.session.add(new_user)
        db.session.commit()
        # Send the confirmation link the user needs before they can log in.
        send_confirmation_email(new_user)
        flash('Registration successful! Please check your email to confirm your account.', 'success')
        return redirect(url_for('loggedout.login'))

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

# -- EMAIL ROUTES --

# confrim email
@loggedout.route("/confirm/<token>")
def confirm_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    user = load_confirm_token(token)
    if user is None:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for('loggedout.resend_confirmation'))
    if user.email_confirmed:
        flash('Account already confirmed. Please log in.', 'info')
        return redirect(url_for('loggedout.login'))

    user.email_confirmed = True
    db.session.commit()
    flash('Your account has been confirmed!', 'success')
    # Clicking the emailed link proves they own the address, so log them straight in.
    login_user(user)
    return redirect(url_for('loggedin.dash'))

# resend confirmation email
@loggedout.route("/resend_confirmation", methods=['GET', 'POST'])
def resend_confirmation():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    form = ResendConfirmationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Only send when there's an account that still needs confirming.
        if user and not user.email_confirmed:
            send_confirmation_email(user)
        # For security, we won't reveal whether the email exists (or is already
        # confirmed) — always flash the same generic message.
        flash('If an unconfirmed account with that email exists, a confirmation email has been sent.', 'info')
        return redirect(url_for('loggedout.login'))
    return render_template("loggedout/resend_confirmation.html", form=form)

#forgot password route
@loggedout.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Send password reset email
            send_password_reset_email(user)
        # For security, we won't reveal whether the email exists or not. Just flash a generic message.
        flash('If an account with that email exists, a password reset link has been sent.', 'info')
        return redirect(url_for('loggedout.login'))
    return render_template("loggedout/forgot_password.html", form=form)

#reset password route
@loggedout.route("/reset-password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('loggedin.dash'))
    user = load_reset_token(token)
    if user is None:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('loggedout.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.new_password.data
        # Receiving the reset link proves they control the address, so an account
        # that never got confirmed shouldn't be left locked out of login.
        user.email_confirmed = True
        db.session.commit()  # This will also invalidate the token since it checks the password hash
        flash('Your password has been reset! Please log in with your new password.', 'success')
        return redirect(url_for('loggedout.login'))
    
    return render_template("loggedout/reset_password.html", form=form)
