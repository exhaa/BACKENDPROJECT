from flask import jsonify
from service.user_service import fetch_users, fetch_user


def get_users():
    return jsonify(fetch_users())


def get_user(user_id):
    user = fetch_user(user_id)

    if user:
        return jsonify(user)

    return jsonify({
        "success": False,
        "message": "User not found"
    }), 404