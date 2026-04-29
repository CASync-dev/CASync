from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import select, text
from app import db
from app.models import User

api_friends = Blueprint("api_friends", __name__)

@api_friends.route("/api/getusers", methods=["POST", "GET"])
@login_required
def getusers():
    # Username search: 3 letters should give a range of usernames with those three letters
    # Email search: Must be exact for privacy reasons
    data = request.get_json()
    if 'search' not in data or len(data['search']) < 1:
        print("invalid search")
        return jsonify({"Error: Invalid search"}), 400
    # If it's an email
    if '@' in data['search']:
        print("Email detected!")
        searchmail = data['search']
        query = text("SELECT users.username FROM users WHERE users.email = :e")
        param = {"e":searchmail}
        # There should only be one account per email, if an error raises then there's
        # Something wrong with the datebase...
        # .scalar in case email entered does not have an associated acc
        mail = db.session.scalar(query, param)
        if mail == None:
            print("No email found!")
            return jsonify({'results': 0})
        print("Email found!")
        return jsonify({'results': mail})
    else:
        print("Username detected!")
        # ie. Username
        user = data['search']
        print(user)
        if len(user) < 3:
            print("No user found!")
            # Prevent users from searching using less than 3 letters
            return jsonify({'results': 0})
        print("User found!")
        query = text("SELECT users.username FROM users WHERE users.username = :u_")
        param = {"u_":user}
        users = list(db.session.scalars(query, param).all())
        print(users)
        return jsonify({'results': users})