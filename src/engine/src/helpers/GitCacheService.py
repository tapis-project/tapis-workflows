import os

import git


class GitCacheService:
    def __init__(self, cache_dir):
        self._cache_dir = cache_dir

    def add(self, url: str, directory: str):
        git.Repo.clone_from(url, os.path.join(self._cache_dir, directory.lstrip("/")))

    def repo_exists(self, path):
        print("REPO EXISTS", os.path.exists(path))
        return os.path.exists(path)
    
    def update(self, directory):
        print("GIT PULL", directory)
        git.cmd.Git(directory).pull()

    def add_or_update(self, url, directory):
        print("ADD OR UPDATE", directory)
        if not self.repo_exists(directory):
            print("CREATING", url, directory)
            self.add(url, directory)
            return
        print("UPDATING", directory)
        self.update(directory)