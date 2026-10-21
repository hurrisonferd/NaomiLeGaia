"""ScampOS ChatOS dual-guest integration and boundary tests."""
import importlib.util,json,unittest
from pathlib import Path
REPO=Path(__file__).resolve().parents[5]
CORE=REPO/"GaiaOS/SystemsOS/Core/ScampOS"
API=REPO/"api"
spec=importlib.util.spec_from_file_location("dual_scamp_host",API/"gaiaos_scamp_chat.py")
host=importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)
RIN="SCAMP-001 RIN-RIN 😈"
HELTI="SCAMP-002 HELTI-SKELTI 🕸️"

class Message:
    def __init__(self,role,content):self.role,self.content=role,content

def fixture():
    registry=json.loads((CORE/"CURRENT.json").read_text(encoding="utf-8"))
    b={"guests":{},"knowledge_threads":json.loads((CORE/"Knowledge/HELTI-SKELTI-FACTS.v1.json").read_text(encoding="utf-8"))}
    for id,paths in registry["guests"].items():
        b["guests"][id]={
            "character":json.loads((REPO/paths["character"]).read_text(encoding="utf-8")),
            "policy":json.loads((REPO/paths["policy"]).read_text(encoding="utf-8"))
        }
    return b

class HostTests(unittest.TestCase):
    def setUp(self):self.bundle=fixture()
    def choose(self,text,rin=.99,helti=.99,extra=()):
        return host.decide(list(extra)+[Message("user",text)],self.bundle,
                           roll={"SCAMP-001":rin,"SCAMP-002":helti})

    def test_rin_spontaneous_with_new_exact_header(self):
        d=self.choose("Hello",rin=0)
        self.assertEqual(d["header"],RIN)
        self.assertEqual(d["reason"],"CHANCE")
        self.assertEqual(host.validate_output(RIN+"\nI have opinions.",d)["status"],"PASS_GUEST_RENDERED")

    def test_helti_spontaneous_without_topic(self):
        d=self.choose("What should I eat tonight?",helti=0)
        self.assertEqual(d["guest_id"],"SCAMP-002")
        self.assertEqual(d["header"],HELTI)
        self.assertTrue(d["fact"]["line"])
        self.assertTrue(d["fact"]["url"].startswith("https://"))
        self.assertIn(d["fact"]["line"],host.model_instruction(d))
        self.assertEqual(host.validate_output(HELTI+"\n"+d["fact"]["line"],d)["status"],"PASS_GUEST_RENDERED")

    def test_helti_exact_fact_not_fabricated(self):
        d=self.choose("The sky is pink",helti=0)
        with self.assertRaises(ValueError):
            host.validate_output(HELTI+"\nI can read your files.",d)

    def test_no_guest_without_selection(self):
        d=self.choose("hello")
        self.assertFalse(d["appear"])
        self.assertEqual(host.validate_output("The answer is yes.",d)["status"],"PASS_NO_GUEST_SELECTED")
        with self.assertRaises(ValueError):
            host.validate_output(HELTI+"\nUninvited",d)

    def test_collision_one_scamp_and_strict_header(self):
        d=self.choose("wow",rin=0,helti=0)
        self.assertTrue(d["collision"])
        wrong=HELTI if d["guest_id"]=="SCAMP-001" else RIN
        with self.assertRaises(ValueError):
            host.validate_output(wrong+"\nWrong speaker",d)
        with self.assertRaises(ValueError):
            host.validate_output(RIN+"\nHi\n"+HELTI+"\nFacts",d)

    def test_named_helti_direct_request(self):
        d=self.choose("Helti-Skelti, speak.",rin=0,helti=.99)
        self.assertEqual(d["guest_id"],"SCAMP-002")
        self.assertEqual(d["reason"],"EXPLICIT")

    def test_new_rin_name_and_legacy_alias(self):
        for alias in ("RIN-RIN","Rin","RINRIN","SCAMP-001"):
            with self.subTest(alias=alias):
                d=self.choose(alias+" get in here",rin=.99,helti=.99)
                self.assertEqual(d["guest_id"],"SCAMP-001")
                self.assertEqual(d["reason"],"EXPLICIT")

    def test_independent_cooldown_from_history(self):
        msgs=[Message("user","hello"),Message("assistant",RIN+"\nComment"),
              Message("user","No one needs to talk")]
        d=host.decide(msgs,self.bundle,roll={"SCAMP-001":0,"SCAMP-002":0})
        self.assertEqual(d["guest_id"],"SCAMP-002")
        self.assertEqual(d["evaluations"]["SCAMP-001"]["reason"],"COOLDOWN")

    def test_individual_mute_persists_until_unmute(self):
        previous=[Message("user","Mute RIN-RIN"),Message("assistant","Fine")]
        d=self.choose("Normal conversation",rin=0,helti=0,extra=previous)
        self.assertEqual(d["guest_id"],"SCAMP-002")
        previous.extend([Message("user","Unmute RIN-RIN"),Message("assistant","Okay")])
        d=self.choose("Normal conversation",rin=0,helti=.99,extra=previous)
        self.assertEqual(d["guest_id"],"SCAMP-001")
        self.assertEqual(d["reason"],"CHANCE")

    def test_helti_mute_persists(self):
        previous=[Message("user","Mute Helti-Skelti"),Message("assistant","Acknowledged")]
        d=self.choose("Testing",rin=.99,helti=0,extra=previous)
        self.assertFalse(d["appear"])

    def test_no_topic_exclusions(self):
        for text in ("Rent is due", "I am grieving", "Urgent medical appointment",
                     "Network knowledge", "I am scared"):
            with self.subTest(text=text):
                d=self.choose(text,rin=.99,helti=0)
                self.assertEqual(d["guest_id"],"SCAMP-002")

    def test_source_and_boot_paths_wired(self):
        a=(API/"gaiaos_api.py").read_text(encoding="utf-8")
        b=(API/"gaiaos_app.py").read_text(encoding="utf-8")
        docker=(API/"Dockerfile").read_text(encoding="utf-8")
        for text in ("Characters/RIN-RIN.v1.json","Characters/HELTI-SKELTI.v1.json",
                     "Knowledge/HELTI-SKELTI-FACTS.v1.json",
                     "gaiaos_scamp_chat.decide(","gaiaos_scamp_chat.model_instruction(",
                     "gaiaos_scamp_chat.validate_output("):
            self.assertIn(text,a)
        self.assertIn("SCAMP-002",b)
        self.assertIn('"scampos_guest": _guest_boot_metadata()',b)
        self.assertIn("COPY api/gaiaos_scamp_chat.py ./gaiaos_scamp_chat.py",docker)

    def test_curated_ambiguity_no_forced_motive(self):
        char=self.bundle["guests"]["SCAMP-002"]["character"]
        self.assertEqual(char["motive"],"UNKNOWN_CANONICAL_DO_NOT_RESOLVE")
        self.assertEqual(char["intent_ambiguity"]["teaching"],"UNKNOWN")

if __name__=="__main__":unittest.main()
