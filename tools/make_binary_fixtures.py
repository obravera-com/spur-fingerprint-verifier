"""Regenerate the iscc-data binary fixtures deterministically (seed 24138)."""
import pathlib, random

S = pathlib.Path(__file__).resolve().parent.parent / "fixtures/fingerprint/iscc-data/sources"
S.mkdir(parents=True, exist_ok=True)
rng = random.Random(24138)
ref = bytearray(rng.randbytes(65536))
(S / "ref-blob-01.bin").write_bytes(ref)
(S / "cand-blob-identical.bin").write_bytes(ref)
light = bytearray(ref)
for i in range(0, 65536, 8192):
    light[i] ^= 0xFF
(S / "cand-blob-light-edit.bin").write_bytes(light)
(S / "cand-blob-v2.bin").write_bytes(ref[:20000] + rng.randbytes(8192) + ref[32000:])
heavy = bytearray(ref)
for i in range(0, 65536, 64):
    heavy[i] ^= 0x55
(S / "cand-blob-heavy-edit.bin").write_bytes(heavy)
(S / "neg-blob-unrelated.bin").write_bytes(rng.randbytes(65536))
(S / "neg-blob-recoded.bin").write_bytes(bytes(b ^ 0xA5 for b in ref))
print("written to", S)
