"""Runtime parity: the production image uses a flattened /app source layout.

Prior to this regression, api/gaiaos_scamp_chat.py resolved ROOT two
directories up.  In Docker the module is /app/gaiaos_scamp_chat.py, so it
looked for /GaiaOS/SystemsOS/... and every real /chat request returned 500.
"""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
CORE = "GaiaOS/SystemsOS/Core/ScampOS"
HEADERS = {
    "SCAMP-001": "SCAMP-001 RIN-RIN 😈",
    "SCAMP-002": "SCAMP-002 HELTI-SKELTI 🕸️",
}

class Message:
    def __init__(self, role, content):
        self.role, self.content = role, content

def import_guest_host(path):
    spec = importlib.util.spec_from_file_location("scamp_test_flat_docker_host",path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def source_bundle():
    current=json.loads((REPO/CORE/"CURRENT.json").read_text(encoding="utf-8"))
    bundle={"guests":{}}
    for guest_id,info in current["guests"].items():
        bundle["guests"][guest_id]={
            "character":json.loads((REPO/info["character"]).read_text(encoding="utf-8")),
            "policy":json.loads((REPO/info["policy"]).read_text(encoding="utf-8")),
        }
    return bundle

class TestProductionDockerGuestRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix="gaia-scamp-flat-docker-")
        cls.app=(Path(cls.temp.name)/"app").resolve()
        cls.app.mkdir()
        shutil.copy2(REPO/"api/gaiaos_scamp_chat.py",cls.app/"gaiaos_scamp_chat.py")
        shutil.copytree(REPO/CORE,cls.app/CORE)
        cls.guest_host=import_guest_host(cls.app/"gaiaos_scamp_chat.py")
        cls.bundle=source_bundle()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_root_matches_real_docker_layout(self):
        self.assertEqual(self.guest_host.ROOT,self.app)
        self.assertTrue((self.app/self.guest_host.SCAMP_RUNTIME).is_file())

    def test_each_guest_explicitly_summoned(self):
        for guest_id,prompt in (
            ("SCAMP-001","RIN-RIN, get in here"),
            ("SCAMP-002","HELTI-SKELTI, explain TLS certificate trust"),
        ):
            with self.subTest(guest=guest_id):
                decision=self.guest_host.decide(
                    [Message("user",prompt)],self.bundle,
                    roll={"SCAMP-001":.99,"SCAMP-002":.99})
                self.assertTrue(decision["appear"])
                self.assertEqual(decision["reason"],"EXPLICIT")
                self.assertEqual(decision["header"],HEADERS[guest_id])
                self.assertEqual(decision["guest_id"],guest_id)

    def test_spontaneous_random_draws_select_both(self):
        for guest_id,draw in (
            ("SCAMP-001",{"SCAMP-001":0,"SCAMP-002":.99}),
            ("SCAMP-002",{"SCAMP-001":.99,"SCAMP-002":0}),
        ):
            with self.subTest(guest=guest_id):
                result=self.guest_host.decide(
                    [Message("user","I've made a bowl of noodles")],
                    self.bundle,roll=draw)
                self.assertEqual(result["guest_id"],guest_id)
                self.assertEqual(result["reason"],"CHANCE")
                self.assertEqual(result["interaction_mode"],"intrusion")

    def test_collision_and_silence_are_not_errors(self):
        r=self.guest_host.decide(
            [Message("user","I'm discussing noodles")],
            self.bundle,roll={"SCAMP-001":0,"SCAMP-002":0})
        self.assertTrue(r["collision"])
        self.assertIn(r["guest_id"],HEADERS)
        self.assertEqual(len([r["guest_id"]]),1)
        r=self.guest_host.decide(
            [Message("user","I'm discussing noodles")],
            self.bundle,roll={"SCAMP-001":.99,"SCAMP-002":.99})
        self.assertFalse(r["appear"])

    def test_helti_full_dialogue_and_search_option(self):
        r=self.guest_host.decide(
            [Message("user","Helti-Skelti, explain how TLS certificates work")],
            self.bundle,roll={"SCAMP-001":.99,"SCAMP-002":.99})
        self.assertEqual(r["interaction_mode"],"dialogue")
        self.assertEqual(self.guest_host.response_tool_options(r)["tools"][0]["type"],"web_search")
        content=(HEADERS["SCAMP-002"]+
                 "\nTLS certificates are checked against trust roots.\n"
                 "The certificate authenticates an endpoint, not the honesty "
                 "of the service behind it.")
        self.assertEqual(
            self.guest_host.validate_output(content,r)["status"],
            "PASS_GUEST_RENDERED")

    def test_unchanged_rin_voice_without_web_search(self):
        r=self.guest_host.decide(
            [Message("user","RIN-RIN, say something about cables")],
            self.bundle,roll={"SCAMP-001":.99,"SCAMP-002":.99})
        self.assertEqual(self.guest_host.response_tool_options(r),{})
        self.assertEqual(
            self.guest_host.validate_output(
                HEADERS["SCAMP-001"]+"\nThat cable's not getting any less tangled.",r
            )["status"],"PASS_GUEST_RENDERED")

if __name__=="__main__":
    unittest.main()
