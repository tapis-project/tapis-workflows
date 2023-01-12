import os, logging

from tapipy.tapis import Tapis
from tapipy.errors import InvalidInputError  

from helpers.TapisServiceAPIGateway import TapisServiceAPIGateway
from conf.constants import BASE_WORK_DIR
from errors.archives import ArchiveError
from core.events import Event, EventHandler
from core.events.types import PIPELINE_COMPLETED, PIPELINE_TERMINATED, PIPELINE_FAILED
from utils import trunc_uuid


class TapisSystemArchiver(EventHandler):
    def handle(self, event: Event):
        if event.type in [PIPELINE_COMPLETED, PIPELINE_TERMINATED, PIPELINE_FAILED]:
            event.payload.logger.info(f"[PIPELINE] {event.payload.pipeline.id} [ARCHIVING] {trunc_uuid(event.payload.pipeline.run_id)}")    
            try:
                self.archive(
                    event.payload.archive,
                    event.payload.pipeline,
                    event.payload.group,
                    event.payload.logger
                )
            except ArchiveError as e:
                event.payload.logger.error(f"[PIPELINE] {event.payload.pipeline.id} [ERROR] {trunc_uuid(event.payload.pipeline.run_id)}: {e.message}")
                return
            except Exception as e:
                event.payload.logger.error(f"[PIPELINE] {event.payload.pipeline.id} [ERROR] {trunc_uuid(event.payload.pipeline.run_id)}: {e}")
                return

            event.payload.logger.info(f"[PIPELINE] {event.payload.pipeline.id} [ARCHIVING COMPLETED] {trunc_uuid(event.payload.pipeline.run_id)}")
        

    def archive(self, archive, pipeline, group, logger):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            service_client = tapis_service_api_gateway.get_client()

            perms = service_client.systems.getUserPerms(
                systemId=archive.system_id,
                userName=archive.owner,
                _x_tapis_tenant=group.tenant_id,
                _x_tapis_user=archive.owner
            )
        except InvalidInputError as e:
            raise ArchiveError(f"System '{archive.system_id}' does not exist or you do not have access to it – {e}")
        except Exception as e:
            raise e
        
        # Check that the requesting user had modify permissons on this system
        if "MODIFY" not in perms.names and perms.names.length != 0:
            raise ArchiveError(f"You do not have 'MODIFY' permissions for system '{archive.system_id}'")
        
        # The base archive directory on the system for this pipeline work.
        # Strip the base work dir from the pipline work dir
        base_archive_dir = os.path.join(
            archive.archive_dir.strip("/"),
            pipeline.work_dir.replace(BASE_WORK_DIR, "").strip("/")
        )

        # Transfer all files in the task output dirs to the system
        for task in pipeline.tasks:
            # The archive output dir on the system
            archive_output_dir = os.path.join(base_archive_dir, task.id, "output")
            
            # Create the directories on the system (like an mkdir -p)
            try:
                service_client.files.mkdir(
                    systemId=archive.system_id,
                    path=archive_output_dir,
                    _x_tapis_tenant=group.tenant_id,
                    _x_tapis_user=archive.owner
                )
            except Exception as e:
                logger.error(e)

            # The location in the pipeline service where the outputs for this
            # task are stored
            task_output_dir = os.path.join(pipeline.work_dir, task.id, "output")

            # Upload each file
            # TODO support dirs? Maybe zip it?
            for filename in os.listdir(task_output_dir):
                path_to_file = os.path.join(task_output_dir, filename)
                if os.path.isfile(path_to_file):
                    # Upload the files to the system
                    try:
                        service_client.upload(
                            system_id=archive.system_id,
                            source_file_path=path_to_file,
                            dest_file_path=os.path.join(archive_output_dir, filename),
                            # _x_tapis_tenant=group.tenant_id,
                            # _x_tapis_user=archive.owner,
                            headers={
                                "X-Tapis-Tenant": group.tenant_id,
                                "X-Tapis-User": archive.owner,
                                "X-Tapis-Token": service_client.service_tokens["admin"]["access_token"].access_token
                            }
                        )
                        logger.info(f"[PIPELINE] {pipeline.id} [ARCHIVED] {path_to_file}")
                    except Exception as e:
                        logger.error(e)
