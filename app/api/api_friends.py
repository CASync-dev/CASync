from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import select

from app.models import User

api_friends = Blueprint("api_friends", __name__)

@api_friends.route("api/getusers", methods=["GET"])
@login_required
def getusers():
    # Username search: 3 letters should give a range of usernames with those three letters
    # Email search: Must be exact for privacy reasons
    data = request.args or {}
    if 'search' not in data or len(data['search']) < 1:
        return jsonify({"Error: Invalid search"}), 400
    # If it's an email
    if '@' in data['search']:
        searchmail = data['search']
        query = select(User.username).where(User.email == searchmail).first()

    else:
        # ie. Username
        user = data['search']
        if len(user) < 3:
            # Prevent users from searching using less than 3 letters
            return jsonify({'results': 0})
        query = select(User.username).where(User.username.startswith(user))
    return jsonify({'results': query})