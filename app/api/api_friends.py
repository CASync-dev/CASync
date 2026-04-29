from flask import Blueprint
from flask_login import login_required

api_friends = Blueprint("api_friends", __name__)

@api_friends.route("api/getusers", methods=["GET"])
@login_required
def getusers():
    # Username search: 3 letters should give a range of usernames with those three letters
    # Email search: Must be exact for privacy reasons
    