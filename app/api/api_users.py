from flask import Blueprint, jsonify
from app.models import User

api_users = Blueprint('api_users', __name__)

# -- OTHER API ROUTES

@api_users.route("/api/user")
def api_user():
    user = User.query.first()
    if not user:
        return jsonify({}), 404
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

# This is just a test route to get a list of users
# Upd: Changed def name (Couldn't think of a better name for the blueprint)
@api_users.route("/api/users", methods=["get"])
def api_userlist():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])
