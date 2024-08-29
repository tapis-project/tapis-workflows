from backend.serializers.UUIDSerializer import UUIDSerializer
from backend.serializers.TaskSerializer import TaskSerializer


class PipelineSerializer:
    @staticmethod
    def serialize(pipeline_model, task_models=None):
        pipeline = {}
        pipeline["id"] = pipeline_model.id
        pipeline["description"] = pipeline_model.description
        pipeline["created_at"] = pipeline_model.created_at
        pipeline["updated_at"] = pipeline_model.updated_at
        pipeline["env"] = pipeline_model.env
        pipeline["params"] = pipeline_model.params
        pipeline["uses"] = pipeline_model.uses
        pipeline["enabled"] = pipeline_model.enabled
        pipeline["owner"] = pipeline_model.owner
        pipeline["execution_profile"] = {
            "max_exec_time": pipeline_model.max_exec_time,
            "max_retries": pipeline_model.max_retries,
            "invocation_mode": pipeline_model.invocation_mode,
            "lock_expiration_policy": pipeline_model.lock_expiration_policy,
            "duplicate_submission_policy": pipeline_model.duplicate_submission_policy,
            "retry_policy": pipeline_model.retry_policy
        }
        pipeline["uuid"] = UUIDSerializer.serialize(pipeline_model.uuid)

        # Serialize the task models
        if task_models != None:
            pipeline["tasks"] = [ TaskSerializer.serialize(t) for t in task_models ]

        # TODO Remove when certain these properties are not needed
        pipeline["group"] = UUIDSerializer.serialize(pipeline_model.group.uuid)
        # pipeline["current_run"] = UUIDSerializer.serialize(pipeline_model.current_run)
        # pipeline["last_run"] = UUIDSerializer.serialize(pipeline_model.last_run)
        
        return pipeline