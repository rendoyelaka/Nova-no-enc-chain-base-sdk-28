#!/usr/bin/env python3
"""
encrypt_companion.py — Build-time encryptor for Nova Launcher.

Reads companion.apk, encrypts with AES-256-GCM, writes assets/companion.enc,
and prints the key hex to stdout for build.yml to inject into build.gradle.

Blob layout:  [ 12 bytes IV ][ ciphertext ][ 16 bytes GCM tag ]

Usage:
    python3 tools/encrypt_companion.py <companion.apk> <assets_dir>

Dependencies:
    pip install pycryptodome --break-system-packages
"""

import secrets
import sys
from pathlib import Path

try:
    from Crypto.Cipher import AES
except ImportError:
    print("[X] pycryptodome not found. Run: pip install pycryptodome --break-system-packages")
    sys.exit(1)

COMPANION_APK = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("companion.apk")
NOVA_ASSETS   = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("app/src/main/assets")
OUTPUT_ENC    = NOVA_ASSETS / "companion.enc"
KEY_FILE      = Path("build/companion_key.txt")

KEY_SIZE = 32
IV_SIZE  = 12


def encrypt_blob(data: bytes, key: bytes) -> bytes:
    iv = secrets.token_bytes(IV_SIZE)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return iv + ciphertext + tag


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

    NOVA_ASSETS.mkdir(parents=True, exist_ok=True)
    OUTPUT_ENC.write_bytes(blob)
    print(f"[OK] Written → {OUTPUT_ENC}")

    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_text(key_hex + "\n", encoding="utf-8")
    print(f"[OK] Key saved → {KEY_FILE}")

    # Print key hex to stdout for build.yml to capture
    print(f"COMPANION_KEY_HEX={key_hex}")

    print()
    print("=" * 55)
    print("  ENCRYPTION COMPLETE")
    print(f"  companion.enc → {OUTPUT_ENC}")
    print("=" * 55)


if __name__ == "__main__":
    main()
