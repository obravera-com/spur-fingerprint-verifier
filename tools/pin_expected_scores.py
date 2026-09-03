"""Write expected_score into every manifest from the current implementation.

Run this only when deliberately re-pinning (e.g. after a scheme version bump),
then review the diff. CI compares recomputed scores against these pins.
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
from spur_fingerprint_verifier import verify

root = pathlib.Path(__file__).resolve().parent.parent / "fixtures/fingerprint"
for mp in sorted(root.rglob("manifest.json")):
    m = json.loads(mp.read_text(encoding="utf-8"))
    for v in m["vectors"]:
        ref = (mp.parent / v["reference"]).read_bytes()
        cand = (mp.parent / v["candidate"]).read_bytes()
        r = verify.match(m["scheme_id"], ref, cand, v.get("threshold", m["default_threshold"]), v.get("unit", "document"))
        v["expected_score"] = r.score
    mp.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    print("pinned", mp)
