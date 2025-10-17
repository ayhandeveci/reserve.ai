
def validate_json_output(obj, expected_keys=None):
    # liberal validator: ensure obj is dict and contains expected_keys
    if obj is None:
        return {}
    if not isinstance(obj, dict):
        return {"raw": str(obj)}
    if expected_keys:
        for k in expected_keys:
            obj.setdefault(k, [] if k in ("segments","features") else "")
    return obj
