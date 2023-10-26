import os, sys


if __name__ == "__main__":
    sys.path.append("/mnt/open-workflow-engine/pipeline/task/src")
    os.chdir(os.path.dirname(os.environ.get("_OWE_ENTRYPOINT_FILE_PATH")))
    exec(open(os.environ.get("_OWE_ENTRYPOINT_FILE_PATH")).read())