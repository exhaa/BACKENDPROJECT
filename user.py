import time
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import psutil

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger
from flask_cors import CORS
from redis_client import redis_client
from middleware.cache import invalidate_cache
from middleware.cache import cache_response

from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta
import os
import bcrypt
import uuid
import logging
from flask import Flask, request, jsonify, g
from extensions import db, migrate

from middleware.auth import authenticate_token

from model.post import Post
from validators.user_validator import RegisterSchema
from middleware.validation import validate

import bleach
from logging_config import setup_logging
from middleware.sanitizer import remove_nosql_operators
from job_queue import queue
from tasks import send_email_task
from rq import Retry
from redis_connection import redis_conn
from socket_handler import socketio

import socket_events  # noqa: F401

# ---------------------- APP SETUP ----------------------
# eygittgit add .

load_dotenv(dotenv_path=".env")
setup_logging()
logger = logging.getLogger(__name__)


app = Flask(__name__)
metrics = PrometheusMetrics(app)

metrics.info(
    "app_info",
    "Application information",
    version="1.0"
)

memory_usage = Gauge(
    "app_memory_usage_bytes",
    "Application memory usage in bytes"
)

@app.route("/metrics", methods=["GET"])
def metrics_endpoint():
    return generate_latest(), 200, {
        "Content-Type": CONTENT_TYPE_LATEST
    }
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

@app.before_request
def add_correlation_id():
    g.correlation_id = request.headers.get(
        "X-Correlation-ID",
        str(uuid.uuid4())
    )
    process = psutil.Process()
    memory_usage.set(process.memory_info().rss)

@app.after_request
def add_correlation_header(response):
    response.headers["X-Correlation-ID"] = g.correlation_id
    return response


socketio.init_app(app)
Swagger(app)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"]}})
limiter = Limiter(key_func=get_remote_address, app=app)
 
# if not app.config.get("TESTING"):
#     Talisman(app)
def check_database():
    try:
        db.session.execute(db.text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def check_redis():
    try:
        start_time = time.time()

        redis_conn.ping()

        latency = round(
            (time.time() - start_time) * 1000,
            2
        )

        return {
            "status": "healthy",
            "latency_ms": latency
        }

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")

        return {
            "status": "unhealthy",
            "latency_ms": None
        }


@app.route("/healthz", methods=["GET"])
def healthz():

    database_ok = check_database()
    redis_result = check_redis()

    overall_healthy = (
        database_ok
        and redis_result["status"] == "healthy"
    )

    return jsonify({
        "status": "healthy" if overall_healthy else "unhealthy",

        "database": {
            "status": "healthy" if database_ok else "unhealthy"
        },

        "redis": redis_result
    }), 200 if overall_healthy else 503


@app.route("/readyz", methods=["GET"])
def readyz():

    database_ok = check_database()
    redis_result = check_redis()

    application_ready = (
        database_ok
        and redis_result["status"] == "healthy"
    )

    return jsonify({
        "status": "ready" if application_ready else "not_ready",

        "database": {
            "status": "healthy" if database_ok else "unhealthy"
        },

        "redis": redis_result
    }), 200 if application_ready else 503

db.init_app(app)
migrate.init_app(app, db)


@app.route("/send-email", methods=["POST"])
def send_email():
    job = queue.enqueue(send_email_task, "esha@gmail.com")

    return {"message": "Email queued", "job_id": job.id}


# ---------------------- USER MODEL ----------------------


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    passwordHash = db.Column(db.String(255), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    posts = db.relationship(
        "Post", backref="user", lazy=True, cascade="all, delete-orphan"
    )


# ---------------------- REGISTER ----------------------

@app.route("/auth/register", methods=["POST"])
@validate(RegisterSchema)
def register():

    logger.info(
        "Registration request received",
        extra={
            "route": request.path,
            "method": request.method,
            "correlation_id": g.correlation_id
        }
    )

    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: Esha
            email:
              type: string
              example: esha@test.com
            password:
              type: string
              example: Password123
    responses:
      201:
        description: User registered successfully
      400:
        description: Email already exists
    """

    data = request.get_json()
    data = remove_nosql_operators(data)

    data["name"] = bleach.clean(data["name"])
    data["email"] = bleach.clean(data["email"])

    existing_user = User.query.filter_by(email=data["email"]).first()

    if existing_user:
        logger.warning(
            "Registration failed: email already exists",
            extra={
                "route": request.path,
                "method": request.method,
                "correlation_id": g.correlation_id
            }
        )
        return jsonify({"message": "Email already exists"}), 400

    hashed_password = bcrypt.hashpw(
        data["password"].encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    new_user = User(
        name=data["name"],
        email=data["email"],
        passwordHash=hashed_password
    )

    db.session.add(new_user)
    db.session.commit()

    job = queue.enqueue(
        send_email_task,
        new_user.email,
        retry=Retry(max=4, interval=[5, 10, 20, 40])
    )

    invalidate_cache("/users*")

    logger.info(
        "User registered successfully",
        extra={
            "route": request.path,
            "method": request.method,
            "correlation_id": g.correlation_id
        }
    )

    return jsonify({
        "message": "User registered successfully",
        "job_id": job.id
    }), 201


@app.route("/posts", methods=["POST"])
@authenticate_token
def create_post():
    """
    Create Post
    ---
    tags:
      - Posts
    security:
      - Bearer: []
    responses:
      201:
        description: Post created successfully
    """

    data = request.get_json()
    data["title"] = bleach.clean(data["title"])
    data["content"] = bleach.clean(data["content"])

    post = Post(title=data["title"], content=data["content"], user_id=g.user["userId"])

    db.session.add(post)
    db.session.commit()

    return jsonify({"message": "Post created successfully"}), 201


# ---------------------- LOGIN ----------------------


@app.route("/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():

    logger.info(
        "Login request received",
        extra={
            "route": request.path,
            "method": request.method,
            "correlation_id": g.correlation_id
        }
    )

    """
    User Login
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: esha@test.com
            password:
              type: string
              example: Password123
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """

    data = request.get_json()

    user = User.query.filter_by(email=data["email"]).first()

    if user is None:
        logger.warning(
            "Login failed: invalid email",
            extra={
                "route": request.path,
                "method": request.method,
                "correlation_id": g.correlation_id
            }
        )

        return jsonify({"message": "Invalid email or password"}), 401

    if not bcrypt.checkpw(
        data["password"].encode("utf-8"),
        user.passwordHash.encode("utf-8")
    ):
        logger.warning(
            "Login failed: invalid password",
            extra={
                "route": request.path,
                "method": request.method,
                "correlation_id": g.correlation_id
            }
        )

        return jsonify({"message": "Invalid email or password"}), 401

    payload = {
        "userId": user.id,
        "role": "user",
        "exp": datetime.utcnow() + timedelta(hours=1),
    }

    token = jwt.encode(
        payload,
        os.getenv("JWT_SECRET"),
        algorithm="HS256"
    )

    logger.info(
        "User login successful",
        extra={
            "route": request.path,
            "method": request.method,
            "correlation_id": g.correlation_id
        }
    )

    return jsonify({
        "message": "Login successful",
        "token": token
    }), 200


@app.route("/users/<int:id>", methods=["GET"])
@authenticate_token
@cache_response(timeout=300)
def get_user(id):
    """
    Get User
    ---
    tags:
      - Users
    parameters:
      - in: path
        name: id
        type: integer
        required: true
    responses:
      200:
        description: User details
      404:
        description: User not found
    """

    user = User.query.get(id)

    if user is None:
        return jsonify({"message": "User not found"}), 404

    return (
        jsonify(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "createdAt": user.createdAt,
            }
        ),
        200,
    )


# ---------------------- UPDATE USER ----------------------


@app.route("/users/<int:id>", methods=["PUT"])
@authenticate_token
def update_user(id):
    """
    Update User
    ---
    tags:
      - Users
    responses:
      200:
        description: User updated successfully
    """

    user = User.query.get(id)
    if user is None:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    if "name" in data:
        data["name"] = bleach.clean(data["name"])

    if "email" in data:
        data["email"] = bleach.clean(data["email"])

        print("DATA =", data)
        print("TYPE =", type(data))

    if not isinstance(data, dict):
        return jsonify({"message": "Invalid JSON"}), 400

    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)

    db.session.commit()
    db.session.refresh(user)
    print("Updated Name:", user.name)
    print("Updated Email:", user.email)

    invalidate_cache(f"/users/{id}*")
    invalidate_cache("/users*")

    return jsonify({"message": "User updated successfully"}), 200


# ---------------------- DELETE USER ----------------------


@app.route("/users/<int:id>", methods=["DELETE"])
@authenticate_token
def delete_user(id):
    """
    Delete User
    ---
    tags:
      - Users
    responses:
      200:
        description: User deleted successfully
    """

    user = User.query.get(id)

    if user is None:
        return jsonify({"message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    invalidate_cache(f"/users/{id}*")
    invalidate_cache("/users*")
    return jsonify({"message": "User deleted successfully"}), 200


# ---------------------- MY POSTS ----------------------


@app.route("/posts/my-posts", methods=["GET"])
@authenticate_token
def my_posts():
    """
    Get My Posts
    ---
    tags:
      - Posts
    responses:
      200:
        description: List of posts
    """

    posts = Post.query.filter_by(user_id=g.user["userId"]).all()

    post_list = []

    for post in posts:
        post_list.append({"id": post.id, "title": post.title, "content": post.content})

    return jsonify(post_list), 200


# ---------------------- USERS WITH POSTS ----------------------


@app.route("/users-with-posts", methods=["GET"])
def users_with_posts():
    """
    Users With Posts
    ---
    tags:
      - Relations
    responses:
      200:
        description: Users and their posts
    """

    users = User.query.all()

    result = []

    for user in users:
        result.append(
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "posts": [
                    {"id": post.id, "title": post.title, "content": post.content}
                    for post in user.posts
                ],
            }
        )

    return jsonify(result), 200


# ---------------------- USER POSTS ----------------------


@app.route("/users/<int:id>/posts", methods=["GET"])
def get_user_posts(id):
    """
    User Posts
    ---
    tags:
      - Relations
    responses:
      200:
        description: Posts of a specific user
    """

    user = User.query.get(id)

    if user is None:
        return jsonify({"message": "User not found"}), 404

    posts = []

    for post in user.posts:
        posts.append({"id": post.id, "title": post.title, "content": post.content})

    return jsonify(posts), 200


@app.route("/join/users-posts", methods=["GET"])
def users_posts_join():

    results = (
        db.session.query(User.name, Post.title)
        .join(Post, User.id == Post.user_id)
        .all()
    )

    data = []

    for name, title in results:
        data.append({"name": name, "title": title})

    return jsonify(data), 200


# ---------------------- RUN APP ----------------------
@app.route("/cache")
def cache():
    redis_client.set("message", "Hello Redis!", ex=60)

    message = redis_client.get("message")

    return {"message": message}
print("\nREGISTERED ROUTES:")
print(app.url_map)
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
