from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user
from app.models import User
from app import db

api_users = Blueprint('api_users', __name__)

# Delete User Route (So users can delete their accounts if they want to)
  # needs to properly delete the user and cascade delete any related data (events, settings, etc.) to avoid orphaned data in the database
@api_users.route("/api/changeusername", methods=["POST"])
def change_username():
    # Awaiting groups/friends page
    print("Placeholder :)")

@api_users.route("/api/changeemail", methods=["POST"])
def change_email():
    data = request.get_json()
    if 'newemailaddress' not in data or len(data['newemailaddress']) < 1:
        return jsonify({"error": "Invalid Address"})
    # Checking if its an email
    if '@' not in data['newemailaddress']:
        return jsonify({"error": "Not an Email"})
    newmail = data['newemailaddress']
    # SQLAlchemy should make sure that an email isn't being used twice in the database,
    # But for extra precaution I've added a check here as well.
    # Also lets us give an custom error message 
    check = User.query.filter(User.email == newmail).first()
    if current_user.id == check.id:
        return jsonify({"error": "Already your email!"})
    # If check is not None
    if check:
        return jsonify({"error": "Email already associated with another account."})
    
    # If all checks are passed, the email is free and can be used by the current user.
    current_user.email = newmail
    db.session.commit()
    return jsonify({"success": "Email successfully changed."})


@api_users.route("/accountdeletion", methods=["POST"])
def accdelpage():
    return render_template("/settings/removeacc.html")

# -- OTHER API ROUTES (Deprecated)
# This file is for any API routes related to users, such as fetching user info, updating settings, etc.
# @api_users.route("/api/user")
# def api_user():
#     user = User.query.first()
#     if not user:
#         return jsonify({}), 404
#     return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

# # This is just a test route to get a list of users
# # Upd: Changed def name (Couldn't think of a better name for the blueprint)
# @api_users.route("/api/users", methods=["get"])
# def api_userlist():
#     users = User.query.all()
#     return jsonify([u.to_dict() for u in users])