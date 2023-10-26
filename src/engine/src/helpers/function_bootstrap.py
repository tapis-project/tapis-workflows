import os, sys


sys.path.append("/mnt/open-workflow-engine/pipeline/task/src/owe_python_sdk")
exec(open(os.envrion.get("_OWE_ENTRYPOINT_FILE_PATH")).read())