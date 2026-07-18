from flask import jsonify
from model.user_model import users


def get_users():
    return jsonify(users)


def get_user(user_id):
    for user in users:
        if user["id"] == user_id:
            return jsonify(user)

    return jsonify({"success": False, "message": "User not found"}), 404
