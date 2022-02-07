from backend.services.Authenticator import authenticator


def auth(fn):
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper