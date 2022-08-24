import requests


def github_cred_validator(creds):
    try:
        resp = requests.get(
            "https://api.github.com/user",
            auth=(
                creds["username"],
                creds["personal_access_token"],
            )
        )

        if resp.status_code not in range(200, 300):
            return False

        data = resp.json()

        if "login" in data.keys() and creds["username"] != data["login"]:
            return False

    except Exception as e:
        raise e

    return True

def dockerhub_cred_validator(creds):
    return True

def validate_by_type(_type, creds):
    try:
        if _type == "github":
            return github_cred_validator(creds)
        elif _type == "dockerhub":
            return dockerhub_cred_validator(creds)
        else:
            return True
    except Exception as e:
        raise e