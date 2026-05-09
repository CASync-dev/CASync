from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import select
from app import db
from app.models import Group, User


api_groups = Blueprint("api_groups", __name__)


@api_groups.route("/api/group/friends", methods=["GET"])
@login_required
def group_get_friends():
    friends = current_user.get_friends()  # list of user objects

    # Format response to JSON for browsers
    return jsonify({"friends": [friend.public_dict() for friend in friends]}), 200

@api_groups.route("/api/group/create", methods=["POST"])
@login_required
def create_group():
    # Reads JSON payload from frontend
    data = request.get_json()

    # Extracts data
    name = data.get("name")  # name of new group
    friends_added = data.get(
        "list", []
    )  # list of usernames/friends to include in group; missing = empty list

    # Validate group name exist
    if not name:
        return jsonify({"error": "Group name required"}), 400

    group = Group(group_name=name)
    group.members.append(current_user)  # adds current user (creator of group) to group

    # Adds the rest of friends to group
    for friend_username in friends_added:
        user = User.query.filter_by(username=friend_username).first()
        if user and user != current_user:
            group.members.append(user)  # populates many-to-many relationship

    db.session.add(group)
    db.session.commit()

    return jsonify({"success": True, "group": group.to_dict()})
