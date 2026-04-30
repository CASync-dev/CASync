from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import select, text
from app import db
from app.models import User, Friendship

api_friends = Blueprint("api_friends", __name__)

@api_friends.route("/api/getusers", methods=["POST", "GET"])
@login_required
def getusers():
    # Username search: 3 letters should give a range of usernames with those three letters
    # Email search: Must be exact for privacy reasons
    data = request.get_json()
    if 'search' not in data or len(data['search']) < 1:
        return jsonify({"Error: Invalid search"}), 400
    # If it's an email
    if '@' in data['search']:
        searchmail = data['search']
        mail = User.query.filter_by(email=searchmail).all()
        if mail == []:
            return jsonify({'results': 0})
        # the user model has a to dict method that converts the user object to a dictionary.
        return jsonify({'results': [u.to_dict() for u in mail]})
    else:
        # ie. Username
        user = data['search']
        if len(user) < 3:
            # Prevent users from searching using less than 3 letters
            return jsonify({'results': 0})
        users = User.query.filter(User.username.contains(user)).all()
        if users == []:
            return jsonify({'results': 0})
        return jsonify({'results': [u.to_dict() for u in users]})
    
@api_friends.route("/api/requestfriend", methods=["POST"])
@login_required
# This route is for sending a friend request to another user. It checks if the username provided in the request exists 
# in the database, if so, it creates a new friend request entry in the database and returns a success message. 
# If the username does not exist, it returns an error message.
def requestfriend():
    data = request.get_json()
    # Check if the username is provided in the request data
    if 'username' not in data:
        return jsonify({"Error: Invalid username"}), 400
    username = data['username']
    # This checks if the user exists, this shoulnt be a probelm as the frontend only allows searhcing for existing users but just in case.
    user_id = db.session.scalar(select(User.id).where(User.username == username))
    if user_id == None:
        return jsonify({"Error: User not found"}), 404
    # Create a new friend request entry in the database
    new_request = Friendship(requester_id=current_user.id, receiver_id=user_id, status='pending', created_at=db.func.now(), updated_at=db.func.now())
    db.session.add(new_request)
    db.session.commit()
    
    return jsonify({"message": f"Friend request sent to {username}!"}), 200