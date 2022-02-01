import string, random, os

def random_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k = 15))

build_context = {
    "pipeline": {
        "id": random_id(),
        "actions": [
            {
                "id": random_id(),
                "stage": "post_build",
                "description": "Send a webhook notification to freetail that the image was pushed successfully",
                "http_method": "post",
                "name": "Notify Kube Cluster",
                "type": "webhook",
                "url": "http://someurl.com",
            }
        ],
        "auto_build": False,
        "branch": "develop",
        "cache": False,
        "context": {
            "branch": "develop",
            "credential": {
                "id": "some-credential-id",
                "name": "My Github Credential",
                "description": "Username and personal access token to pull repository code from Github", 
                "data": {
                    "token": os.environ["REPO_TOKEN"]
                }
            },
            "dockerfile_path": "src/Dockerfile",
            "repo": "nathandf/jscicd-image-demo-private",
            # "repo": "nathandf/jscicd-image-demo",
            "sub_path": None,
            "type": "github",
            "visibility": "private",
            # "visibility": "public",
        },
        "destination": {
            "credential": {
                "id": "some-credential-id",
                "name": "My Dockerhub Secret",
                "description": "Username and password(or access token) to push Dockerhub",
                "data": {
                    "username": os.environ["REGISTRY_USER"],
                    "token": os.environ["REGISTRY_TOKEN"]
                }
            },
            "tag": None,
            "url": "nathandf/jscicd-kaniko-test",
        },
        "event_type": "push",
        "name": "Test Pipeline"
    },
    "event": {
        "commit": "This is a commit message with directives [build|custom_tag:custom-tagV0.1]",
        "commit_sha": "37c2a4f"
    },
    "directives": {}
}