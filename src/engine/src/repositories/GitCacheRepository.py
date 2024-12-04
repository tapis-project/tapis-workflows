import os

import git


class GitCacheRepository:
    def __init__(self, cache_dir):
        self._cache_dir = cache_dir

    def add(self, url: str, directory: str, branch=None):
        kwargs = {}
        if branch != None:
            kwargs["branch"] = branch
        git.Repo.clone_from(url, os.path.join(self._cache_dir, directory.lstrip("/")), **kwargs)

    def repo_exists(self, path):
        return os.path.exists(os.path.join(self._cache_dir, path.lstrip("/")))
    
    def update(self, directory, branch=None):
        git.cmd.Git(os.path.join(self._cache_dir, directory.lstrip("/"))).pull()

    def add_or_update(self, url, directory, branch=None):
        if not self.repo_exists(directory):
            self.add(url, directory, branch)
            return
        
        self.update(directory, branch)