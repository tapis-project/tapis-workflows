from backend.services.TapisAuthenticator import authenticator


def auth(fn):
    def wrapper(*args, **kwargs):
        fn(*args, **kwargs)

    return wrapper