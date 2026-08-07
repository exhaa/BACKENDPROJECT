import os
import jwt
from functools import wraps
from flask import request, jsonify, g
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")


def authenticate_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        # Read Authorization header
        auth_header = request.headers.get("Authorization")

        # Check if token exists
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "message": "Token is missing"
            }), 401

        # Extract token
        token = auth_header.split(" ")[1]

        try:
            print("JWT_SECRET =", JWT_SECRET)
            print("TOKEN =", token)

            decoded = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"]
            )

            print("DECODED =", decoded)

            g.user = decoded

        except jwt.ExpiredSignatureError:
            print("ERROR: Token has expired")
            return jsonify({
                "success": False,
                "message": "Token has expired"
            }), 403

        except jwt.InvalidTokenError as e:
            print("JWT ERROR:", e)
            return jsonify({
                "success": False,
                "message": "Invalid token"
            }), 403

        return f(*args, **kwargs)

    return decorated