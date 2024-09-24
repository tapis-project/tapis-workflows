import os


class FileSystemDAO:
    def get(self, path: str):
        # Check that the specified output file exists
        if not os.path.isfile(path):
            raise Exception(f"File {path} not found")

        # Grab the value of the output from the file
        result = None
        with open(path, "r") as file:
            result = file.read()

        return result
    
    def write(self, path: str, contents):
        contents = contents if contents != None else ""
        with open(path, "w") as file:
            file.write(contents)

    def writebin(self, path: str, contents):
        contents = contents if contents != None else ""
        with open(path, "wb") as file:
            file.write(contents)