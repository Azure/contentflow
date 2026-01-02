import json
import datetime

def make_safe_json(data):
    """
    Recursively process the input data to ensure it is JSON serializable.
    Non-serializable objects are converted to their string representation.
    """
    if isinstance(data, dict):
        return {key: make_safe_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_safe_json(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(make_safe_json(item) for item in data)
    elif isinstance(data, set):
        return [make_safe_json(item) for item in data]
    elif data is None:
        return None
    elif isinstance(data, datetime.datetime):
        return data.isoformat()
    elif isinstance(data, (int, float, str, bool)):
        return data
    elif isinstance(data, bytes):
        return data.decode('utf-8', errors='replace')
    elif hasattr(data, '__dict__'):
        return make_safe_json(vars(data))
    elif hasattr(data, '__str__'):
        return str(data)
    else:
        try:
            # Try to serialize the data to JSON
            json.dumps(data)
            return data
        except (TypeError, OverflowError):
            # If serialization fails, convert to string
            return str(data)

