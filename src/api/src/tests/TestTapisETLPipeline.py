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
        serialized = {
            "REMOTE_OUTBOX": json.dumps(self.pipeline.remote_outbox.dict()),
            "LOCAL_INBOX": json.dumps(self.pipeline.local_inbox.dict()),
            "LOCAL_OUTBOX": json.dumps(self.pipeline.local_outbox.dict()),
            "REMOTE_INBOX": json.dumps(self.pipeline.remote_inbox.dict()),
        }

    def testETLEnvBuilderUtil(self):
        env = build_etl_pipeline_env(self.pipeline)
        
        assert type(env) == dict
        assert env.get("REMOTE_OUTBOX_MANIFEST_GENERATION_POLICY").get("value") == "auto_one_per_file"
        assert env.get("LOCAL_INBOX_MANIFEST_GENERATION_POLICY") == None
        assert env.get("LOCAL_OUTBOX_MANIFEST_GENERATION_POLICY").get("value") == "auto_one_for_all"
        assert env.get("REMOTE_INBOX_MANIFEST_GENERATION_POLICY") == None

if __name__ == "__main__":
    unittest.main()


