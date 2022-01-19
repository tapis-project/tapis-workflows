import string
import random

build_context = {
    "id": ''.join(random.choices(string.ascii_uppercase + string.digits, k = 15)),
    "branch": "main",
    #"context": "git://github.com/nathandf/jscicd-image-demo.git",
    #"dockerfile_path": "src/Dockerfile",
    #"destination": "nathandf/jscicd-kaniko-test:local-test",
    "context": "alpine",
    "dockerfile_path": "Dockerfile",
    "destination": None,
    "event_type": "push",
    "name": "test-deployment",
    "repository_url": "https://github.com/nathandf/jscicd-image-demo"
}