import json

from tapipy.tapis import Tapis
from owe_python_sdk.runtime import execution_context as ctx

system_id = ctx.get_input("TAPIS_SYSTEM_ID")
username = ctx.get_input("TAPIS_USERNAME")
password = ctx.get_input("TAPIS_PASSWORD")
base_url = ctx.get_input("TAPIS_BASE_URL")
file_ref = ctx.get_input("TAPIS_FILE_REF")

try:
    t = Tapis(
        base_url=base_url,
        username=username,
        password=password
    )

    t.get_tokens()
except Exception as e:
    ctx.stderr(1, e.message)

file_ref_obj = json.loads(file_ref)

contents = t.files.getContents(systemId=system_id, path=file_ref_obj["path"])

ctx.set_output(f"contents", contents)

ctx.stdout("Hello stdout - use file refs")