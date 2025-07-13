from typing import List

from django.db import DatabaseError, IntegrityError, OperationalError
from backend.models import TaskTag, Task
from backend.services.Service import Service


class TaskTagService(Service):
    def __init__(self):
        Service.__init__(self)

    def batch_create(self, task, tags: List[str] = []):
        try:
            for tag in tags:
                TaskTag.objects.create(
                    value=tag,
                    task=task
                )
        except (IntegrityError, OperationalError, DatabaseError) as e:
            print(f"Failed create tag '{tag}': {e}", flush=True)
            raise e
        except Exception as e:
            print(f"Unexpected Error when creating task tag '{tag}': {e}", flush=True)
            raise e

        return task
    
    def update_by_task_model(self, task_model: Task, tags_patch: List[str]):
        # Remove duplicate values
        tags_patch = list(set(tags_patch))

        try:
            # Delete all tags if an empty list is provided
            if len(tags_patch) == 0:
                TaskTag.objects.filter(task=task_model).delete()
                return
        except Exception as e:
            print(f"Failed to delete all tags for task '{task_model.id}': {e}")
            raise e
        
        try:
            # Fetch all tags for this task from the database
            tag_models = list(TaskTag.objects.filter(
                task=task_model,
            ))
        except Exception as e:
            print(f"Failed to fetch all tags for task '{task_model.id}' during task tag update: {e}")
            raise e
        
        existing_tags = [tag_model.value for tag_model in tag_models]

        tags_to_create = []
        for tag in tags_patch:
            if tag not in existing_tags:
                tags_to_create.append(tag)

        # Create all the new tags
        try:
            self.batch_create(task_model, tags_to_create)
        except Exception as e:
            print(f"Failed to batch create tags during update of task '{task_model.id}': {e}")
            raise e

        tags_to_delete = []
        for tag in existing_tags:
            if tag not in tags_patch:
                tags_to_delete.append(tag)

        # Delete tags from the existing tags list that are not present in the 
        # tags patch list
        for tag in tags_to_delete:
            try:
                TaskTag.objects.delete(
                    value=tag,
                    task=task_model
                )
            except Exception as e:
                print(f"Failed to create tag '{tag}' for task '{task_model.id}': {e}")
                raise e

service = TaskTagService()
