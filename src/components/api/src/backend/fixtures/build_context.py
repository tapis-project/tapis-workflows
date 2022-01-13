build_context = {
    "branch": "main",
    "context": "git://github.com/nathandf/jscicd-image-demo.git",
    "dockerfile_path": "src/Dockerfile",
    "destination": "nathandf/jscicd-kaniko-test:local-test",
    "event_type": "push",
    "name": "test-deployment",
    "repository_url": "https://github.com/nathandf/jscicd-image-demo"
}