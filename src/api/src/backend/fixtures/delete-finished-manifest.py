#-------- Workflow Context start: DO NOT REMOVE ----------------
from wf import execution_context as ctx
#-------- Workflow Context end: DO NOT REMOVE ------------------

from tapipy.tapis import Tapis

try: 
    # NOTE The "base_url" param should be passed in the "params" object of a 
    # workflow submission request
    t = Tapis(
        base_url=ctx.get_input("TAPIS_BASE_URL"),
        username=ctx.get_input("TAPIS_USERNAME"),
        password=ctx.get_input("TAPIS_PASSWORD")
    )

    manifest_file_path = ctx.get_input("manfiestFilePath")

    t.files.delete(
        systemId=ctx.get_input("TAPIS_SYSTEM_ID"),
        path=manifest_file_path
    )

    ctx.stdout(0, f"Manfiest file successfully deleted: {manifest_file_path}")

except Exception as e:
    # Saves stack trace to stderr and exits with code 1
    ctx.error(1, str(e))