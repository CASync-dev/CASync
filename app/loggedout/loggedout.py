from flask import Blueprint, render_template, redirect, url_for

loggedout = Blueprint('loggedout', __name__, template_folder='../templates/loggedout', static_folder='../static')

@loggedout.route("/")
def index():
    return render_template('loggedout/homepage.html')

@loggedout.route("/login")
def login():
    return render_template("loggedout/login.html")

@loggedout.route("/register")
def register():
    return render_template("loggedout/register.html")

# Added /home as a redirect to index, otherwise you can access the homepage from both routes and it's kinda odd
@loggedout.route("/home")
def home():
    return redirect(url_for('loggedout.index'))

@loggedout.route("/faq")
def faq():
    return render_template("loggedout/faq.html")

@loggedout.route("/contactus")
def contactus():
    return render_template("loggedout/contact-us.html")

