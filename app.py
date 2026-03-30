from flask import Flask, render_template, jsonify
from extensions import db
from models import User, Event

app = Flask(__name__)
# Configure the database URI and initialize the database
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

# Login, register, homepage and faq currently have a different style from the other webpages.
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/home")
def home():
    return render_template("homepage.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")


# API routes - at the moment they return json responses but thats not long term
@app.route("/api/events")
def api_events():
    events = Event.query.all()
    return jsonify([e.to_dict() for e in events])

@app.route("/api/user")
def api_user():
    user = User.query.first()
    if not user:
        return jsonify({}), 404
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email})


# Error handling
@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404



if __name__ == "__main__":
    app.run(debug=True, port=8080)
