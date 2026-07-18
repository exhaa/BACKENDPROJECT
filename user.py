from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)

load_dotenv(dotenv_path=".env")

print("DATABASE_URL =", os.getenv("DATABASE_URL"))

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------------- GET ALL USERS ----------------------
@app.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()

    user_list = []

    for user in users:
        user_list.append(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "createdAt": user.createdAt,
            }
        )

    return jsonify(user_list)


# ---------------------- CREATE USER ----------------------
@app.route("/users", methods=["POST"])
def create_user():

    data = request.get_json()

    existing_user = User.query.filter_by(email=data["email"]).first()

    if existing_user:
        return jsonify({"message": "Email already exists"}), 400

    new_user = User(name=data["name"], email=data["email"])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201


# ---------------------- UPDATE USER ----------------------
@app.route("/users/<int:id>", methods=["PUT"])
def update_user(id):

    user = User.query.get(id)

    if user is None:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()

    user.name = data["name"]
    user.email = data["email"]

    db.session.commit()

    return jsonify({"message": "User updated successfully"})


# ---------------------- DELETE USER ----------------------
@app.route("/users/<int:id>", methods=["DELETE"])
def delete_user(id):

    user = User.query.get(id)

    if user is None:
        return jsonify({"message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User deleted successfully"})


if __name__ == "__main__":
    app.run(debug=True)
