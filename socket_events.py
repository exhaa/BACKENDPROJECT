from flask import request
from flask_socketio import (
    emit,
    join_room,
    leave_room
)
from socket_handler import socketio
import jwt
import os


# =====================================================
# DEFAULT NAMESPACE (/)
# =====================================================

@socketio.on("connect")
def handle_connect():
    print(f"Client Connected: {request.sid}")


@socketio.on("disconnect")
def handle_disconnect():
    print(f"Client Disconnected: {request.sid}")


# Join Room
@socketio.on("join_room")
def handle_join_room(data):
    room = data["room"]

    join_room(room)

    emit("joined_room", {
        "room": room,
        "message": f"Joined {room}"
    })


# Leave Room
@socketio.on("leave_room")
def handle_leave_room(data):
    room = data["room"]

    leave_room(room)

    emit("left_room", {
        "room": room,
        "message": f"Left {room}"
    })


# Send message to a specific room
@socketio.on("send_room_message")
def handle_room_message(data):
    emit(
        "room_message",
        {
            "message": data["message"],
            "room": data["room"]
        },
        to=data["room"]
    )


# =====================================================
# CHAT NAMESPACE (/chat)
# =====================================================

@socketio.on("connect", namespace="/chat")
def chat_connect(auth):

    token = auth.get("token") if auth else None

    if not token:
        print("No token provided")
        return False

    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )

        print(f"Authenticated User: {payload['userId']}")

    except jwt.InvalidTokenError:
        print("Invalid JWT")
        return False

    print(f"Chat Connected: {request.sid}")


@socketio.on("disconnect", namespace="/chat")
def chat_disconnect():
    print(f"Chat Namespace Disconnected: {request.sid}")


# Custom chat message event
@socketio.on("send_message", namespace="/chat")
def receive_message(data):
    room = data["room"]

    print("Chat:", data)

    emit(
        "new_message",
        {
            "message": data["message"]
        },
        to=room,
        namespace="/chat"
    )


# Typing indicator
@socketio.on("typing_indicator", namespace="/chat")
def typing(data):
    emit(
        "user_typing",
        {
            "user": data["user"],
            "typing": True
        },
        to=data["room"],
        namespace="/chat"
    )

# =====================================================
# NOTIFICATION NAMESPACE (/notifications)
# =====================================================

@socketio.on("connect", namespace="/notifications")
def notification_connect():
    print(f"Notification Namespace Connected: {request.sid}")


@socketio.on("disconnect", namespace="/notifications")
def notification_disconnect():
    print(f"Notification Namespace Disconnected: {request.sid}")


@socketio.on("send_notification", namespace="/notifications")
def send_notification(data):
    emit(
        "new_notification",
        {
            "notification": data["notification"]
        },
        namespace="/notifications"
    )


# =====================================================
# ERROR HANDLER
# =====================================================

@socketio.on_error_default
def handle_error(e):
    print("Socket Error:", e)