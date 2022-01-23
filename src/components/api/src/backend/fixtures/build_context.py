import string, random, os

build_context = {
    "deployment": {
        "id": ''.join(random.choices(string.ascii_uppercase + string.digits, k = 15)),
        "branch": None,
        "context": "git://github.com/nathandf/jscicd-image-demo.git",
        "context_sub_path": None,
        "dockerfile_path": "src/Dockerfile",
        "destination": "nathandf/jscicd-kaniko-test",
        "event_type": "push",
        "image_tag": None,
        "name": "test-deployment",
        "repository_url": "https://github.com/nathandf/jscicd-image-demo",
        "registry_secret_id": "registry-secret-id",
        "repository_secret_id": "repositry-secret-id",
        "registry_secret": {
            "id": "registry-secret-id",
            "name": "My Dockerhub Secret",
            "description": "Username and password(or access token) to push Dockerhub",
            "secret_type": "PASSWORD",
            "key": os.environ["REGISTRY_USER"],
            "value": os.environ["REGISTRY_TOKEN"]
        },
        "repository_secret": {
            "id": "repository-secret-id",
            "name": "My Github secret",
            "description": "Username and personal access token to pull repository code from Github", 
            "secret_type": "PASSWORD",
            "key": os.environ["REGISTRY_USER"],
            "value": os.environ["REGISTRY_TOKEN"]
        },
    },
    "meta": {
        "commit": "This is a commit message with directives [custom_tag:custom-tagV0.1]",
        "commit_sha": "37c2a4f"
    }
}