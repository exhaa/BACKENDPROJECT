from flask import Flask, request, jsonify

app = Flask(__name__)


# Home Route
@app.route("/")
def home():
    return jsonify({"message": "Welcome to Flask API"})


# Query Parameters
@app.route("/search")
def search():
    query = request.args.get("query")

    return jsonify({"route": "/search", "query": query})


# Path Parameters
@app.route("/users/<int:id>")
def user(id):
    return jsonify({"route": "/users/<id>", "user_id": id})


@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")

    return (
        jsonify({"message": "User created successfully", "name": name, "email": email}),
        201,
    )


if __name__ == "__main__":
    app.run(debug=True, port=3000)
