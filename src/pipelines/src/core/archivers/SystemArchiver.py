import os, logging

from tapipy.tapis import Tapis
from tapipy.errors import InvalidInputError  

from helpers.TapisServiceAPIGateway import TapisServiceAPIGateway
from conf.configs import BASE_WORK_DIR
from errors.archives import ArchiveError


class SystemArchiver:
    def archive(self, archive, pipeline, group, base_url):
        try:
            tapis_service_api_gateway = TapisServiceAPIGateway()
            service_client = tapis_service_api_gateway.get_client()
        
            # Get a token for the user that owns the archive
            res = service_client.tokens.create_token(
                account_type="user",
                token_tenant_id=group.tenant_id,
                token_username=archive.owner,
                access_token_ttl=4400,
                generate_refresh_token=False,
                use_basic_auth=False,
                _tapis_set_x_headers_from_service=True)

            jwt = res.access_token.access_token

            # Initialize the tapipy client
            client = Tapis(
                base_url=base_url,
                jwt=jwt
            )

            # Get the requesters permissions
            res = client.systems.getUserPerms(
                systemId=archive.system_id,
                userName=archive.owner
            )
        except InvalidInputError as e:
            logging.error(e)
            raise ArchiveError(f"System '{archive.system_id}' does not exist or you do not have access to it.")
        except Exception as e:
            raise e

        # Check that the requesting user had modify permissons on this system
        if "MODIFY" not in res.names:
            raise ArchiveError(f"You do not have 'MODIFY' permissions for system '{archive.system_id}'")

        # Create the archive directories on the system. Strip the base work dir
        # from the pipline work dir
        base_archive_dir = os.path.join(
            archive.archive_dir,
            pipeline.work_dir.lstrip(BASE_WORK_DIR)
        )

        # Transfer all files in the task output dirs to the system
        for task in pipeline.tasks:
            # The archive output dir on the system
            archive_output_dir = os.path.join(base_archive_dir, task.id, "output")

            # The location in the pipeline service where the outputs for this
            # task are stored
            task_output_dir = os.path.join(pipeline.work_dir, task.id, "output")

            # Upload each file
            # TODO support dirs? Maybe zip it?
            for filename in os.listdir(task_output_dir):
                path_to_file = os.path.join(task_output_dir, filename)
                if os.path.isfile(path_to_file):
                    # Upload the files to the system
                    client.upload(
                        system_id=archive.system_id,
                        source_file_path=path_to_file,
                        dest_file_path=os.path.join(archive_output_dir, filename)
                    )
