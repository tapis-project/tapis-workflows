from typing import List

from django.db import DatabaseError, IntegrityError, OperationalError
from backend.models import PipelineTag, Pipeline
from backend.services.Service import Service


class PipelineTagService(Service):
    def __init__(self):
        Service.__init__(self)

    def batch_create(self, pipeline, tags: List[str] = []):
        try:
            for tag in tags:
                PipelineTag.objects.create(
                    value=tag,
                    pipeline=pipeline
                )
        except (IntegrityError, OperationalError, DatabaseError) as e:
            print(f"Failed create tag '{tag}': {e}", flush=True)
            raise e
        except Exception as e:
            print(f"Unexpected Error when creating pipeline tag '{tag}': {e}", flush=True)
            raise e

        return pipeline

    def update_by_pipeline_model(self, pipeline_model: Pipeline, tags_patch: List[str]):
        # Remove duplicate values
        tags_patch = list(set(tags_patch))

        try:
            # Delete all tags if an empty list is provided
            if len(tags_patch) == 0:
                PipelineTag.objects.filter(pipeline=pipeline_model).delete()
                return
        except Exception as e:
            print(f"Failed to delete all tags for pipeline '{pipeline_model.id}': {e}")
            raise e
        
        try:
            # Fetch all tags for this pipeline from the database
            tag_models = list(PipelineTag.objects.filter(
                pipeline=pipeline_model,
            ))
        except Exception as e:
            print(f"Failed to fetch all tags for pipeline '{pipeline_model.id}' during pipeline tag update: {e}")
            raise e
        
        existing_tags = [tag_model.value for tag_model in tag_models]

        tags_to_create = []
        for tag in tags_patch:
            if tag not in existing_tags:
                tags_to_create.append(tag)

        # Create all the new tags
        for tag in tags_to_create:
            try:
                PipelineTag.objects.create(
                    value=tag,
                    pipeline=pipeline_model
                )
            except Exception as e:
                print(f"Failed to create tag '{tag}' for pipeline '{pipeline_model.id}': {e}")
                raise e

        tags_to_delete = []
        for tag in existing_tags:
            if tag not in tags_patch:
                tags_to_delete.append(tag)

        # Delete tags from the existing tags list that are not present in the 
        # tags patch list
        for tag in tags_to_delete:
            try:
                PipelineTag.objects.delete(
                    value=tag,
                    pipeline=pipeline_model
                )
            except Exception as e:
                print(f"Failed to create tag '{tag}' for pipeline '{pipeline_model.id}': {e}")
                raise e


service = PipelineTagService()
