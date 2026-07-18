from flask import jsonify


def register_error_handlers(app):

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": "Bad Request"}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Resource Not Found"}), 404

    @app.errorhandler(Exception)
    def handle_exception(error):
        return jsonify({"success": False, "error": str(error)}), 500
