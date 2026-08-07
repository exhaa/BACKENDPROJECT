import bleach

def sanitize_input(data):
    if isinstance(data, dict):

        return {
            key: bleach.clean(str(value))
            for key, value in data.items()
        }

    return data
def remove_nosql_operators(data):

    if isinstance(data, dict):

        return {
            key: remove_nosql_operators(value)
            for key, value in data.items()
            if not key.startswith("$")
        }

    return data