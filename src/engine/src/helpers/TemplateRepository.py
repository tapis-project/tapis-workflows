import os, json

from urllib.parse import urlparse

from .GitCacheService import GitCacheService
from owe_python_sdk.schema import Uses


class TemplateRepository:
    def __init__(self, cache_dir: str):
        # Clone git repository specified on the pipeline.uses if exists
        self.cache_dir = cache_dir
        self.git_cache_service = GitCacheService(cache_dir=cache_dir)
    
    def get_by_uses(self, uses: Uses):
        self.git_cache_service.add_or_update(
            uses.source.url,
            self._url_to_directory(uses.source.url)
        )

        template_root_dir = os.path.join(self.cache_dir, uses.source.url)
        
        try:
            # Open the owe-config.json file
            with open(os.path.join(template_root_dir, "owe-config.json")) as file:
                owe_config = json.loads(file.read())

            # Open the etl pipeline schema.json
            with open(
                os.path.join(
                    template_root_dir,
                    owe_config.get(uses.name).get("path")
                )
            ) as file:
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