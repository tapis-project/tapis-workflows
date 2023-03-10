import json

from tapipy.tapis import Tapis
from owe_python_sdk.runtime import execution_context as ctx

system_id = ctx.get_input("TAPIS_SYSTEM_ID")
username = ctx.get_input("TAPIS_USERNAME")
password = ctx.get_input("TAPIS_PASSWORD")
manifest_files_path = ctx.get_input("MANIFEST_FILES_PATH")
base_url = ctx.get_input("TAPIS_BASE_URL")

try:
    t = Tapis(
        base_url=base_url,
        username=username,
        password=password
    )

    t.get_tokens()
except Exception as e:
    ctx.stderr(1, e.message)

files = t.files.listFiles(systemId=system_id, path=manifest_files_path)

for i, file in enumerate(files):
    ctx.set_output(f"file{i}", json.dumps(file.__dict__))

ctx.stdout("Hello stdout")