import os, logging

from tapipy.tapis import Tapis
from tapipy.errors import InvalidInputError

from conf.configs import TAPIS_BASE_URL, BASE_WORK_DIR
from errors.archives import ArchiveError


class SystemArchiver:
    def archive(self, archive, pipeline):
        # Get a token for the user that owns the archive
        # TODO Remove below
        jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJqdGkiOiI3OGE3MTVjZi1kN2U0LTQ5YjYtYjM4MS1hMzcwZWRlYTA5MDUiLCJpc3MiOiJodHRwczovL2Rldi5kZXZlbG9wLnRhcGlzLmlvL3YzL3Rva2VucyIsInN1YiI6InRlc3R1c2VyMkBkZXYiLCJ0YXBpcy90ZW5hbnRfaWQiOiJkZXYiLCJ0YXBpcy90b2tlbl90eXBlIjoiYWNjZXNzIiwidGFwaXMvZGVsZWdhdGlvbiI6ZmFsc2UsInRhcGlzL2RlbGVnYXRpb25fc3ViIjpudWxsLCJ0YXBpcy91c2VybmFtZSI6InRlc3R1c2VyMiIsInRhcGlzL2FjY291bnRfdHlwZSI6InVzZXIiLCJleHAiOjE2NTU5NDgwNzgsInRhcGlzL2NsaWVudF9pZCI6bnVsbCwidGFwaXMvZ3JhbnRfdHlwZSI6InBhc3N3b3JkIn0.v3ToTCRx-GNaB-BvxdDwnzE62Bf6M1-7A8yRSvX8IhlxOjlAnXJ3CI8c0DwL1EDBcc9WTmjz45i56j4Nj1NG5Bf1r1DRF1PIaZaD6w1VLVlthV6urMSWMnwB00s2TQl3KX6NfHryvZ_paJCw_hYaQzQHwG2CSOeugr3htLnTBytwhrE8Ig2nyRGoF2D4gAFRCGzngjjo6ZgQ8JQ9hNXmFLKkONnAvJ6RCyjo8VQoqwUwN4EpC1zhjP3rj45Z4vO0aB5vjzkvaj8le8FbXi4OBIEVXcMYMM_gN9SFLJfVUesRlDzFPLuWFkCczDmOj_JiA_0sQ91g3kZeDLJLFzMcfw"
        
        # Initialize the tapipy client
        client = Tapis(
            base_url=TAPIS_BASE_URL,
            jwt=jwt
        )

        try:
            res = client.systems.getUserPerms(
                systemId=archive.system_id,
                userName=archive.owner
            )
        except InvalidInputError as e:
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

        # Transfer all files in the action output dirs to the system
        for action in pipeline.actions:
            # The archive output dir on the system
            archive_output_dir = os.path.join(base_archive_dir, action.id, "output")

            logging.debug(archive_output_dir)

            # The location in the pipeline service where the outputs for this
            # action are stored
            action_output_dir = os.path.join(pipeline.work_dir, action.id, "output")

            logging.debug(action_output_dir)

            # Upload each file
            # TODO support dirs? Maybe zip it?
            for filename in os.listdir(action_output_dir):
                path_to_file = os.path.join(action_output_dir, filename)
                if os.path.isfile(path_to_file):
                    # Upload the files to the system
                    print(f"Uploading {path_to_file} \n", end="")
                    client.upload(
                        system_id=archive.system_id,
                        source_file_path=path_to_file,
                        dest_file_path=os.path.join(archive_output_dir, filename)
                    )
