import os, json

from urllib.parse import urlparse

from core.repositories import GitCacheRepository
from owe_python_sdk.schema import Uses


class TemplateRepository:
    def __init__(self, cache_dir: str):
        # Clone git repository specified on the pipeline.uses if exists
        self.cache_dir = cache_dir
        self.git_cache_repo = GitCacheRepository(cache_dir=cache_dir)
    
    def get_by_uses(self, uses: Uses):
        git_repo_dir = self._url_to_directory(uses.source.url)
        self.git_cache_repo.add_or_update(
            uses.source.url,
            git_repo_dir
        )

        template_root_dir = os.path.join(self.cache_dir, git_repo_dir)
        
        try:
            # Open the owe-config.json file
            with open(os.path.join(template_root_dir, "owe-config.json")) as file:
                owe_config = json.loads(file.read())

            # Open the etl pipeline schema.json
            template_ref = owe_config.get(uses.name, None)
            if template_ref == None:
                raise Exception(f"Template reference for key '{uses.name}' not found in the config file")
            
            path_to_template = template_ref.get("path", None)
            if path_to_template == None:
                raise Exception(f"The template reference object for template '{uses.name}' is undefined")
            
            with open(os.path.join(template_root_dir, path_to_template)) as file:
                template = json.loads(file.read())
        except Exception as e:
            raise Exception(f"Templating configuration Error (owe-config.json): {str(e)}")
            
        return template
    
    def _url_to_directory(self, url):
        parsed_url = urlparse(url)
        directory = os.path.join(
            parsed_url.hostname,
            *[part.lstrip("/") for part in parsed_url.path.split("/")]
        )

        return directory