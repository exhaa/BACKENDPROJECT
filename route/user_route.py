from flask import Blueprint
from controler.user_controler import get_users, get_user

user_bp = Blueprint("user_bp", __name__)

user_bp.route("/users", methods=["GET"])(get_users)
user_bp.route("/users/<int:user_id>", methods=["GET"])(get_user)
