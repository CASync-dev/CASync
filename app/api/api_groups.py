from flask import Blueprint, request
from flask_login import login_required


api_groups = Blueprint("api_groups", __name__)

@api_groups.route("/api/group/create", methods=['POST'])
@login_required
def create_group():
    data = request.get_json()
    print(data)