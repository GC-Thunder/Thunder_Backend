# Reusable util functions
# └── tasks/

def safe_get(d: dict, path: list):
    for key in path:
        d = d.get(key, {})
    return d or None