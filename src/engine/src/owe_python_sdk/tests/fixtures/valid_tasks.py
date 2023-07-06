image_build = {
    "id": "build",
    "type": "image_build",
    "description": "build mpm image",
    "builder": "kaniko",
    "input": {
        "from-env": {
            "type": "string",
            "value_from": {
                "env": "TEST"
            }
        },
        "from-params": {
            "type": "string",
            "value_from": {
                "params": "TEST"
            }
        },
        "from-task-output": {
            "type": "string",
            "value_from": {
                "task_output": {
                    "task_id": "some-id",
                    "output_id": "test"
                }
            }
        },
        "from-host": {
            "type": "string",
            "value_from": {
                "host": {
                    "type": "kubernetes_secret",
                    "name": "some-secret-name",
                    "field_selector": "{this.is.a.field.selector}"
                }
            }
        },
        "from-secret": {
            "type": "string",
            "value_from": {
                "secret": {
                    "engine": "tapis-security-kernel",
                    "pk": "some-sk-secret-name",
                    "field_selector": "{this.is.a.field.selector}"
                }
            }
        }
    },
    "context": {
        "type": "github",
        "url": "joestubbs/mpm",
        "branch": "master",
        "build_file_path": "/Dockerfile",
        "visibility": "public"
    },
    "destination": {
        "type": "dockerhub",
        "url": "nathandf/mpm-test",
        "tag": "test",
        "visibility": "private",
        "credentials": {
            "username": "nathandf",
            "token": "a190f902-d418-491a-9abc-c22eff2aa335"
        }
    }
}

request = {
    "id": "cat-facts-request-1",
    "type": "request",
    "url": "https://catfact.ninja",
    "http_method": "get"
}