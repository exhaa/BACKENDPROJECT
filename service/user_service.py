from model.user_model import users

def fetch_users():
    return users

def fetch_user(user_id):
    for user in users:
        if user["id"] == user_id:
            return user
    return None