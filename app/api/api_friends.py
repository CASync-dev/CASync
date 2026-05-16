from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import select, text
from app import db
from app.models import User, Friendship, Event
from datetime import datetime, timezone

api_friends = Blueprint("api_friends", __name__)

@api_friends.route("/api/getusers", methods=["POST", "GET"])
@login_required
def getusers():
    # Username search: 3 letters should give a range of usernames with those three letters
    # Email search: Must be exact for privacy reasons
    data = request.get_json()
    if 'search' not in data or len(data['search']) < 1:
        return jsonify({"Error": "Invalid search"}), 400
    # If it's an email
    if '@' in data['search']:
        searchmail = data['search']
        mail = User.query.filter(User.email == searchmail).first()
        # .first() in case email entered does not have an associated acc
        # Dont include the user themselves in search results
        if mail is None or mail.id == current_user.id:
            return jsonify({'results': 0})
        # Check if a friendship already exists with the searched user, if so, don't return them in search results
        existing_friendship = Friendship.query.filter(
            ((Friendship.sender_id == current_user.id) & (Friendship.recipient_id == mail.id)) |
            ((Friendship.sender_id == mail.id) & (Friendship.recipient_id == current_user.id))
        ).first()
        if existing_friendship and existing_friendship.status != 'rejected':
            return jsonify({'results': 0})
        # We call the public_dict method to only return the id and username of the user from the USer object.
        return jsonify({'results': [mail.public_dict()]})
    else:
        # ie. Username
        user = data['search']
        if len(user) < 3:
            # Prevent users from searching using less than 3 letters
            return jsonify({'results': 0})
        users = User.query.filter(User.username.contains(user)).all()
        # Dont include the user themselves in search results
        users = [u for u in users if u.id != current_user.id]
        # Filter out users that already have a friendship with the current user
        users = [u for u in users if not Friendship.query.filter(
            ((Friendship.sender_id == current_user.id) & (Friendship.recipient_id == u.id) & (Friendship.status != 'rejected')) |
            ((Friendship.sender_id == u.id) & (Friendship.recipient_id == current_user.id) & (Friendship.status != 'rejected'))
        ).first()]
        if users == []:
            return jsonify({'results': 0})
        return jsonify({'results': [u.public_dict() for u in users]})
    
@api_friends.route("/api/requestfriend", methods=["POST"])
@login_required
# This route is for sending a friend request to another user. It checks if the username provided in the request exists 
# in the database, if so, it creates a new friend request entry in the database and returns a success message. 
# If the username does not exist, it returns an error message.
def requestfriend():
    data = request.get_json()
    # Check if the user_id is provided in the request data
    if 'user_id' not in data:
        return jsonify({"error": "Invalid user_id"}), 400
    user_id = int(data['user_id'])
    # This checks if the user exists, this shoulnt be a probelm as the frontend only allows searhcing for existing users but just in case.
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    # Check if a friend request already exists between the current user and the target user
    existing_request = Friendship.query.filter(
        ((Friendship.sender_id == current_user.id) & (Friendship.recipient_id == user_id)) |
        ((Friendship.sender_id == user_id) & (Friendship.recipient_id == current_user.id))
    ).first()
    if existing_request:
        if existing_request.status == 'pending':
            return jsonify({"error": "Friend request already pending"}), 400
        elif existing_request.status == 'accepted':
            return jsonify({"error": "You are already friends"}), 400
        elif existing_request.status == 'rejected':
            existing_request.status = 'pending'
            existing_request.sender_id = current_user.id
            existing_request.recipient_id = user_id
            existing_request.created_at = db.func.now()
            db.session.commit()
            return jsonify({"message": f"Friend request sent to {user.username}!"}), 200
    # Create a new friend request entry in the database
    new_request = Friendship(sender_id=current_user.id, recipient_id=user_id, status='pending', created_at=db.func.now())
    db.session.add(new_request)
    db.session.commit()
    return jsonify({"message": f"Friend request sent to {user.username}!"}), 200

@api_friends.route("/api/acceptfriend", methods=["POST"])
@login_required
def acceptfriend():
    data = request.get_json()
    if 'request_id' not in data:
        return jsonify({"Error": "Invalid request_id"}), 400
    request_id = data['request_id']
    # Check if the friend request exists and is pending
    # can only accept friend requests that are sent to the current user, not ones they sent themselves
    friend_request = Friendship.query.filter(
        ((Friendship.id == request_id) & (Friendship.status == 'pending'))
    ).first()
    if not friend_request:
        return jsonify({"Error": "No pending friend request found"}), 404
    # Check if the current user is the recipient of the friend request
    if friend_request.recipient_id != current_user.id:
        return jsonify({"Error": "You can only accept friend requests sent to you"}), 403
    # Update the friend request status to accepted
    friend_request.status = 'accepted'
    friend_request.accepted_at = db.func.now()
    friend = User.query.get(friend_request.sender_id)
    db.session.commit()
    return jsonify({"message": f"Friend request accepted from {friend.username}!"}), 200

@api_friends.route("/api/rejectfriend", methods=["POST"])
@login_required
def rejectfriend():
    data = request.get_json()
    if 'request_id' not in data:
        return jsonify({"Error": "Invalid request_id"}), 400
    request_id = data['request_id']
    # Check if the friend request exists and is pending
    # can only reject friend requests that are sent to the current user, not ones they sent themselves
    friend_request = Friendship.query.filter(
        ((Friendship.id == request_id) & (Friendship.status == 'pending'))
    ).first()
    if not friend_request:
        return jsonify({"Error": "No pending friend request found"}), 404
    # Check if the current user is the recipient of the friend request
    if friend_request.recipient_id != current_user.id:
        return jsonify({"Error": "You can only reject friend requests sent to you"}), 403
    # Update the friend request status to rejected
    friend_request.status = 'rejected'
    db.session.commit()
    return jsonify({"message": "Friend request rejected."}), 200

@api_friends.route("/api/removefriend", methods=["POST"])
@login_required
def removefriend():
    data = request.get_json()
    if 'friend_id' not in data:
        return jsonify({"Error": "Invalid friend_id"}), 400
    friend_id = int(data['friend_id'])
    # Check if a friendship exists between the current user and the target user
    friendship = Friendship.query.filter(
        ((Friendship.sender_id == current_user.id) & (Friendship.recipient_id == friend_id)) |
        ((Friendship.sender_id == friend_id) & (Friendship.recipient_id == current_user.id))
    ).first()
    if not friendship or friendship.status != 'accepted':
        return jsonify({"Error": "You are not friends with this user"}), 404
    db.session.delete(friendship)
    db.session.commit()
    return jsonify({"message": "Friend removed."}), 200


# friends status api
@api_friends.route("/api/friendsstatus", methods=["GET"])
@login_required
def friends_status():
    now_str = request.args.get('now')
    if not now_str:
        return jsonify({"Error": "Missing 'now' parameter"}), 400
    
    now = datetime.fromisoformat(now_str)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    friends = current_user.get_friends()
    result = []

    for friend in friends:
        # Check if friend has an event right now
        current_event = Event.query.filter_by(user_id=friend.id, going=True).filter(
            Event.start_time <= now,
            Event.end_time >= now
        ).first()
        in_class = current_event is not None

        # If in class, return negative minutes remaining so the frontend knows to show "In Class Now"
        next_start = None
        if in_class:
            next_start = -int((current_event.end_time - now).total_seconds() // 60)
        else:
            next_event = Event.query.filter_by(user_id=friend.id, going=True).filter(
                Event.start_time > now
            ).order_by(Event.start_time.asc()).first()
            if next_event:
                next_start = int((next_event.start_time - now).total_seconds() // 60)
            
        
        result.append({
            'id': friend.id,
            'username': friend.username,
            "email": friend.email,
            'avatar_url': friend.avatar(150),
            'in_class': in_class,
            'minutes_until_next': next_start
        })
    
    return jsonify(result)