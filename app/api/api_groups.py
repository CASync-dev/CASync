from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import select
from app import db
from app.models import Group, User


api_groups = Blueprint("api_groups", __name__)


# Waiting until friends are implemented
@api_groups.route("/api/group/create", methods=['POST'])
@login_required
def create_group():
    data = request.get_json()
    group = Group(group_name = data['name'])
    for name in data['list']:
        print("Not finished, here to get rid of stupid python error")

@api_groups.route("/api/group/friends", methods=['GET'])
@login_required
def group_get_friends():
    friends = current_user.get_friends() # list of user objects
    
    # Format response to JSON for browsers
    return jsonify({
        "friends": [friend.public_dict() for friend in friends]
    }), 200
