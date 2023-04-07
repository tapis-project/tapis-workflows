#-------- Workflow Context start: DO NOT REMOVE ----------------
from wf import execution_context as ctx
#-------- Workflow Context end: DO NOT REMOVE ------------------

import ntpath
import json
import time
import os

from tapipy.tapis import Tapis

CHECK_FILE_EXT = "md5"
DATA_FILE_EXT = "tar"

class Manifest():
    def __init__(self, filename, path, files=[], is_processing=False):
        self.filename = filename
        self.path = path
        self.files = files
        self.is_processing = is_processing

    def save(self, ctx, client):
        # Create the local manifest file to be uploaded
        local_manifest_path = os.path.join(ctx.scratch_dir, manifest.filename)
        with open(local_manifest_path, "w") as file:
            file.write(json.dumps(manifest.__dict__))

        # Upload the local manifest file to the tapis system
        client.upload(
            systemId=ctx.get_input("TAPIS_SYSTEM_ID"),
            source_file_path=local_manifest_path,
            destination_file_path=manifest.path
        )

        return manifest

# Get filename from path. OS agnostic
def get_filename(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def is_check_file(path):
    if get_filename(path).split(".")[-1] == CHECK_FILE_EXT:
        return True
    return False

def build_manifest(data_file):
    # Write a local file with the contents of the manifest
    manifest_filename = "MANIFEST-" + str(time.time)
    remote_manifest_path = os.path.join(ctx.get_input("MANIFESTS"), manifest_filename)

    # Create the manifest object 
    manifest = Manifest(
        filename=manifest_filename,
        path=remote_manifest_path,
        files=[data_file],
        is_pocessing=False
    )
    return manifest

def get_tapis_file_contents_json(path):
    contents = t.getContents(
        systemId=ctx.get_input("TAPIS_SYSTEM_ID"),
        path=path
    ).decode("utf8")

    # Load the manifest object and populate the staged_files list
    return json.loads(contents)

# This list is used to store existing manifests. Once all manfests are populated,
# the first manifest in the list with property "is_processing" == False will be processed
manifests = []

# Fetch existing manifests and create new manifests
try: 
    # NOTE The "base_url" param should be passed in the "params" object of a 
    # workflow submission request
    t = Tapis(
        base_url=ctx.get_input("TAPIS_BASE_URL"),
        username=ctx.get_input("TAPIS_USERNAME"),
        password=ctx.get_input("TAPIS_PASSWORD")
    )

    # Create the manifests directory if it doesn't exist. Equivalent
    # to `mkdir -p`
    t.files.mkdir(
        systemId=ctx.get_input("TAPIS_SYSTEM_ID"),
        path=ctx.get_input("MANIFESTS")
    )

    # Fetch the all manifest files
    files = t.files.listFiles(
        systemId=ctx.get_input("TAPIS_SYSTEM_ID"),
        path=ctx.get_input("MANIFESTS")
    )

    manifest_files = [ file.path for file in files ]
    # Create a list of all paths to data files in the manifest files
    staged_data_files = []
    for path in manifest_files:
        # Load the manifest object and populate the staged_files list
        manifest = Manifest(**json.loads(get_tapis_file_contents_json(path)))
        staged_data_files += manifest.files
        manifests.append(manifest)

    # Fetch the all files from the inbox on the target system
    inbox_files = t.listFiles(
        systemId=ctx.get_input("TAPIS_SYSTEM_ID"),
        path=ctx.get_input("INBOX")
    )

    # Creates new manifests for the data files in the inbox
    for file in inbox_files:
        # Only create manifests for data files
        if not is_check_file(file.path):
            continue
        
        # Use the check file to build the path to the data file
        check_filename = get_filename(file.path)
        data_filename = get_filename(file.path).replace(CHECK_FILE_EXT, DATA_FILE_EXT)
        data_file = file.path.replace(check_filename, data_filename)

        # Create and persist manifests to the tapis system
        if data_file not in staged_data_files:
            manifest = build_manifest(data_file)
            manifest.save(ctx, t)
            manifests.append(manifest.path)

except Exception as e:
    ctx.set_stderr(1, f"Falied to create new manifest: {str(e)}")

# Find and update the manifest is_processing property to true
try:
    # Get the first manifest in the list that is in processing
    next_manifest = None
    for manifest in manifests:
        if manifest.is_processing == False:
            next_manifest = manifest
            break
    
    if next_manifest == None:
        ctx.tasks.skip_next()

    # Update the manifest on the tapis system to "is_processing"
    next_manifest.is_processing = True
    next_manifest.save(ctx, t)

except Exception as e:
    ctx.set_stderr(f"Failed to update manifest to 'is_processing': {e}")


# Convert file_input_arrays dict to string
file_input_arrays = json.dumps(
    [
        {
            "name": "data-file",
            "description": "Data files to be processessed",
            "sourceUrls": next_manifest.files,
            "targetDir": ctx.get_input("TARGET_DIR")
        }
    ]
)

# Set the file_input_arrays to output
ctx.set_output("fileInputArrays", file_input_arrays)

# Set the manifest file path as output
ctx.set_output("manifestFilPath", next_manifest.path)
