from flask import Flask, jsonify, request

app = Flask(__name__)

users = [
    {"id": 1, "name": "Asma", "age": 20},
    {"id": 2, "name": "Mariyum", "age": 22},
    {"id": 3, "name": "Ahmed", "age": 20},
]

next_id = 4


@app.route("/users", methods=["POST"])
def create_user():
    global next_id

    data = request.get_json()

    new_user = {"id": next_id, "name": data["name"], "age": data["age"]}

    users.append(new_user)
    next_id += 1

    return jsonify(new_user), 201


@app.route("/users/<int:id>", methods=["GET"])
def get_user(id):

    for user in users:
        if user["id"] == id:
            return jsonify(user)

    return jsonify({"message": "User not found"}), 404


@app.route("/users/<int:id>", methods=["PUT"])
def update_user(id):

    data = request.get_json()

    for user in users:
        if user["id"] == id:
            user["name"] = data["name"]
            user["age"] = data["age"]

            return jsonify(user)

    return jsonify({"message": "User not found"}), 404


@app.route("/users/<int:id>", methods=["DELETE"])
def delete_user(id):

    for user in users:
        if user["id"] == id:
            users.remove(user)

            return jsonify({"message": "User deleted"})

    return jsonify({"message": "User not found"}), 404


@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(users)


if __name__ == "__main__":
    app.run(debug=True, port=3000)
