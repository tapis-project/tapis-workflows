import string, random, os

build_context = {
    "deployment": {
        "id": ''.join(random.choices(string.ascii_uppercase + string.digits, k = 15)),
        "auto_deploy": False,
        "branch": None,
        "context": "git://github.com/nathandf/jscicd-image-demo.git",
        "context_sub_path": None,
        "dockerfile_path": "src/Dockerfile",
        "destination": "nathandf/jscicd-kaniko-test",
        "event_type": "push",
        "image_tag": None,
        "name": "test-deployment",
        "repository_url": "https://github.com/nathandf/jscicd-image-demo",
        "deployment_credentials": [
            {
                "id": "some-unique-id",
                "credential": {
                    "id": "some-credential-id",
                    "name": "My Dockerhub Secret",
                    "description": "Username and password(or access token) to push Dockerhub",
                    "data": {
                        "username": os.environ["REGISTRY_USER"],
                        "token": os.environ["REGISTRY_TOKEN"]
                    }
                },
                "type": "image_registry",
            },
            {
                "id": "some-unique-id",
                "name": "My Github secret",
                "credential": {
                    "id": "some-credential-id",
                    "name": "My Github Credential",
                    "description": "Username and personal access token to pull repository code from Github", 
                    "data": {
                        "username": os.environ["REGISTRY_USER"],
                        "token": os.environ["REGISTRY_TOKEN"]
                    }
                },
                "type": "repository",
            }
        ],
    },
    "event": {
        "commit": "This is a commit message with directives [deploy|custom_tag:custom-tagV0.1]",
        "commit_sha": "37c2a4f"
    },
    "directives": {}
}