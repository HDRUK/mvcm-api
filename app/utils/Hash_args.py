import hashlib
def hash_args(*args, **kwargs):
    """
    Create a hashable representation of the function's arguments.
    """
    return hashlib.sha256(repr((args, kwargs)).encode()).hexdigest()