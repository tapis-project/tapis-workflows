import string, random, os

def random_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k = 15))

pipeline_context = {
    "build": {
        "id": random_id(),
        "status": "queued"
    },
    "pipeline": {
        "id": random_id(),
        "actions": [
            {
                "id": random_id(),
                "auto_build": False,
                "cache": False,
                "builder": "kaniko",
                "stage": "build",
                "context": {
                    "branch": "develop",
                    "credential": {
                        "sk_id": "some-sk-id",
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
                        "sk_id": "some-sk-id",
                        "data": {
                            "username": os.environ["REGISTRY_USER"],
                            "token": os.environ["REGISTRY_TOKEN"]
                        }
                    },
                    "tag": None,
                    "url": "nathandf/jscicd-kaniko-test",
                },
                "description": "Build the specified image and push it",
                "http_method": None,
                "name": "Build",
                "type": "container_build",
                "url": None,
            },
            {
                "id": random_id(),
                "description": "Send a webhook notification to freetail that the image was pushed successfully",
                "http_method": "post",
                "name": "Notify Kube Cluster",
                "stage": "post_build",
                "type": "webhook_notification",
                "url": "http://someurl.com",
            }
        ],
        "auto_build": False,
        "branch": "develop",
        "builder": "kaniko",
        "cache": False,
        "context": {
            "branch": "develop",
            "credential": {
                "sk_id": "some-sk-id",
                "description": "Username and personal access token to pull repository code from Github", 
                "data": {
                    "username": None,
                    "token": os.environ["REPO_TOKEN"]
                }
            },
            "dockerfile_path": "src/Dockerfile",
            "url": "nathandf/jscicd-image-demo-private",
            # "url": "nathandf/jscicd-image-demo",
            "sub_path": None,
            "type": "github",
            "visibility": "private",
            # "visibility": "public",
        },
        "destination": {
            "credential": {
                "data": {
                    "username": os.environ["REGISTRY_USER"],
                    "token": os.environ["REGISTRY_TOKEN"]
                }
            },
            "tag": None,
            "url": "nathandf/jscicd-kaniko-test",
        },
        "name": "Test Pipeline"
    },
    "event": {
        "commit": "This is a commit message with directives [build|custom_tag:custom-tagV0.1]",
        "commit_sha": "37c2a4f",
        "type": "push",
    },
    "directives": {}
}