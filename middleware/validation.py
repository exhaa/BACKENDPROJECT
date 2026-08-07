from flask import request, jsonify
from pydantic import ValidationError

# Validate request body
def validate(schema):

    def decorator(func):

        def wrapper(*args, **kwargs):

            try:
                data = request.get_json()
                schema(**data)

            except ValidationError as e:
                return jsonify({
                    "success": False,
                    "errors": e.errors()
                }), 400

            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


# Validate URL parameters
def validate_params(schema):

    def decorator(func):

        def wrapper(*args, **kwargs):

            try:
                schema(**kwargs)

            except ValidationError as e:
                return jsonify({
                    "success": False,
                    "errors": e.errors()
                }), 400

            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator