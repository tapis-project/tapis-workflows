from backend.serializers import UUIDSerializer

class BaseTaskSerializer:
    @staticmethod
    def serialize(model):
        task = {}
        task["id"] = model.id
        task["cache"] = model.cache
        task["conditions"] = model.conditions
        task["depends_on"] = model.depends_on
        task["description"] = model.description
        task["flavor"] = model.flavor
        task["input"] = model.input
        task["output"] = model.output
        task["type"] = model.type
        task["uses"] = model.uses
        task["uuid"] = UUIDSerializer.serialize(model.uuid)

        # Build execution profile
        task["execution_profile"] = {
            "flavor": model.falvor,
            "invocation_mode": model.invocation_mode,
            "max_exec_time": model.max_exec_time,
            "max_retries": model.max_retries,
            "retry_policy": model.retry_policy,
        }

        return task