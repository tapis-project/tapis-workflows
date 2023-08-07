from .tasks import request, image_build

standard_workflow = {
    "id": "p1",
    "type": "workflow",
    "archive_ids": [],
    "tasks": [image_build, request],
    "env": {
        "TAPIS_SYSTEM_ID": "my-system-id",
        "MANIFEST_FILES_PATH": "/",
        "TAPIS_USERNAME": "testuser2",
        "TAPIS_PASSWORD": "testuser2"
    }
}