import os
from dotenv import load_dotenv
from flask import Flask, abort
from route.user_route import user_bp
from middleware.error_handler import register_error_handlers

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Load configuration from .env
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
PORT = int(os.getenv("PORT", 5000))

# Register blueprint
app.register_blueprint(user_bp)

# Register global error handlers
register_error_handlers(app)


# Home Route
@app.route("/")
def home():
    return {"success": True, "message": "Welcome to the Flask API"}


# Test 400 Error
@app.route("/bad")
def bad():
    abort(400)


# Test 500 Error
@app.route("/error")
def error():
    x = 10 / 0
    return str(x)


# Run the application
if __name__ == "__main__":
    app.run(debug=True, port=PORT)
