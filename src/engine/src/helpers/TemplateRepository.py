import os,json

from .GitCacheService import GitCacheService
from ..owe_python_sdk.schema import Uses

def TemplateRepository(uses: Uses, cache_dir: str):
    # Clone git repository specified on the pipeline.uses if exists
    git_cache_service = GitCacheService(cache_dir=cache_dir)
    
    git_cache_service.add_or_update(
        uses.source.url,
        # NOTE Using the url as the directory to clone into is intentional
        uses.source.url
    )

    template_root_dir = os.path.join(cache_dir, uses.source.url)
    
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