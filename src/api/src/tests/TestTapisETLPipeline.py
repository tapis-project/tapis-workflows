import unittest, json

from backend.views.http.tapis_etl import TapisETLPipeline
from backend.utils import build_etl_pipeline_env
from tests.utils import load_fixture


class TestTapisETLPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = TapisETLPipeline(**load_fixture("tapis-etl-pipeline.json"))

    def testInstance(self):
        assert type(self.pipeline) == TapisETLPipeline
    
    def testIOBoxToDictSerialization(self):
        json.dumps(self.pipeline.remote_outbox.dict())
        json.dumps(self.pipeline.local_inbox.dict())
        json.dumps(self.pipeline.local_outbox.dict())
        json.dumps(self.pipeline.remote_inbox.dict())

    def testETLEnvBuilderUtil(self):
        env = build_etl_pipeline_env(self.pipeline)
        
        assert type(env) == dict
        assert json.loads(env.get("REMOTE_OUTBOX").get("value")).get("manifests").get("generation_policy") == "auto_one_per_file"
        assert json.loads(env.get("LOCAL_INBOX").get("value")).get("manifests").get("generation_policy") == None
        assert json.loads(env.get("LOCAL_OUTBOX").get("value")).get("manifests").get("generation_policy") == "auto_one_for_all"
        assert json.loads(env.get("REMOTE_INBOX").get("value")).get("manifests").get("generation_policy") == None

if __name__ == "__main__":
    unittest.main()


