import os

import git


class GitCacheService:
    def __init__(self, cache_dir):
        self._cache_dir = cache_dir

    def add(self, url: str, directory: str):
        git.Repo.clone_from(url, os.path.join(self._cache_dir, directory.lstrip("/")))

    def repo_exists(self, path):
        return os.path.exists(self._cache_dir, path.lstrip("/"))
    
    def update(self, directory):
        git.cmd.Git(self._cache_dir, directory.lstrip("/")).pull()

    def add_or_update(self, url, directory):
        if not self.repo_exists(directory):
            self.add(url, directory)
            return
        
        self.update(directory)