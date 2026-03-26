from flask import Flask, render_template

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(debug=True, port=8080)
