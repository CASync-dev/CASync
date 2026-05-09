from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import select
from app import db
from app.models import Group, User, user_group_association


api_groups = Blueprint("api_groups", __name__)


@api_groups.route("/api/group/friends", methods=["GET"])
@login_required
def group_get_friends():
    friends = current_user.get_friends()  # list of user objects

    # Format response to JSON for browsers
    return jsonify({"friends": [friend.public_dict() for friend in friends]}), 200

@api_groups.route("/api/group/add_member", methods=["POST"])
@login_required
def add_member():
    # Reads JSON payload from frontend
    data = request.get_json()

    # Extract data
    group_id = data.get("group_id")
    usernames_to_add = data.get("list", [])

    # Validation for group ID
    if not group_id:
        return jsonify({"error": "group_id is required"}), 400
    try:
        group_id = int(group_id)
    except (TypeError, ValueError):
        return jsonify({"error": "invalid group_id"}), 400
    
    # Validation for at least one user being added
    if not usernames_to_add or len(usernames_to_add) == 0:
        return jsonify({"error": "No users to add"}), 400
    
    # Fetch group
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    if current_user not in group.members:
        return jsonify({"error": "You are not in this group"}), 404
    
    # Track results for detailed response
    added_users = []
    skipped_users = []  # Users already in group
    not_found_users = []  # Users that don't exist in database
    
    # Add each user to the group
    for username in usernames_to_add:
        # Query user by username
        user = User.query.filter_by(username=username).first()
        
        # Edge case: User doesn't exist in database
        if not user:
            not_found_users.append(username)
            continue
        
        # Edge case: User trying to add themselves (redundant but check anyway)
        if user == current_user:
            skipped_users.append(username)
            continue
        
        # Edge case: User already in group
        if user in group.members:
            skipped_users.append(username)
            continue
        
        # All checks passed - add user to group
        group.members.append(user)
        added_users.append(user.to_dict())

         # If no users were actually added, return error
    if len(added_users) == 0:
        return jsonify({
            "error": "No valid users were added",
            "skipped": skipped_users,
            "not_found": not_found_users
        }), 400
    
    # Commit changes to database
    db.session.commit()
    
    # Return success with details about what happened
    return jsonify({
        "success": True,
        "message": f"Added {len(added_users)} member(s) to group",
        "added_users": added_users,
        "skipped": skipped_users,  # Already in group or was current user
        "not_found": not_found_users,  # Don't exist in database
        "group": group.to_dict()
    }), 200

@api_groups.route("/api/group/<int:group_id>", methods=["GET"])
@login_required
def get_group_details(group_id):
    group = Group.query.get(group_id)

    if not group:
        return jsonify({"error": "Could not find group"}), 404

    return jsonify(group.to_dict()), 200

@api_groups.route("/api/group/create", methods=["POST"])
@login_required
def create_group():
    # Reads JSON payload from frontend
    data = request.get_json()

    # Extracts data
    name = data.get("name")  # name of new group
    friends_added = data.get("list", [])  # list of usernames/friends to include in group; missing = empty list

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

# Handles users leaving the group
@api_groups.route("/api/group/leave", methods=["POST"])
@login_required
def leave_group():
    data = request.get_json()
    group_id = data.get("group_id")
    if not group_id:
        return jsonify({"error: Invalid group_id"}), 400
    
    try:
        group_id = int(data['group_id'])
    except (TypeError, ValueError):
        return jsonify({"error: Invalid group_id"}), 400

    # Check if current user exists in the given group (find relationship row)
    # Uses .delete because user_group_association is a raw SQL table, not a python ORM object
    group = Group.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found"}), 404

    if current_user not in group.members:
        return jsonify({"error": "You are not in this group"}), 404
    
    group.members.remove(current_user)

    # Check if group has any remaining members
    if len(group.members) == 0:
        db.session.delete(group)

    db.session.commit()

    return jsonify({"Message": "You have successfully left the group."}), 200
