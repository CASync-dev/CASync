from flask import Flask, render_template
from extensions import db
from models import User, Event

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)
with app.app_context():
    db.create_all()

# Page routes
@app.route("/")
def index():
    return render_template("dash.html")

@app.route("/dash")
def dash():
    return render_template("dash.html")

@app.route("/schedule")
def schedule():
    return render_template("schedule.html")


@app.route("/groups")
def groups():
    return render_template("groups.html")


@app.route("/friends")
def friends():
    return render_template("friends.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")

# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404



if __name__ == "__main__":
    app.run(debug=True, port=8080)
