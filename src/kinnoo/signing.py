"""Signing helpers for archive authenticity workflows."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path


@dataclass(frozen=True)
class KeygenResult:
    private_key_path: Path
    public_key_path: Path
    public_key_fingerprint: str


@dataclass(frozen=True)
class SignatureArtifactResult:
    signature_path: Path
    metadata_path: Path
    public_key_fingerprint: str
    archive_sha256: str


def _crypto_modules() -> tuple[object, object, object]:
    serialization = importlib.import_module("cryptography.hazmat.primitives.serialization")
    ed25519 = importlib.import_module("cryptography.hazmat.primitives.asymmetric.ed25519")
    exceptions = importlib.import_module("cryptography.exceptions")
    return serialization, ed25519, exceptions


def _write_key_bytes(path: Path, payload: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(payload)
    finally:
        # Ensure requested mode is enforced even under restrictive umask.
        os.chmod(path, mode)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def public_key_fingerprint(public_key: object) -> str:
    serialization, _, _ = _crypto_modules()
    raw_public_key = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw_public_key).hexdigest()


def public_key_pem(public_key: object) -> str:
    serialization, _, _ = _crypto_modules()
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")


def generate_ed25519_keypair(private_key_path: Path, public_key_path: Path) -> KeygenResult:
    serialization, ed25519, _ = _crypto_modules()
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    _write_key_bytes(private_key_path, private_key_pem, 0o600)
    _write_key_bytes(public_key_path, public_key_pem, 0o644)

    return KeygenResult(
        private_key_path=private_key_path,
        public_key_path=public_key_path,
        public_key_fingerprint=public_key_fingerprint(public_key),
    )


def load_ed25519_private_key(private_key_path: Path) -> object:
    serialization, ed25519, _ = _crypto_modules()
    payload = private_key_path.read_bytes()
    key = serialization.load_pem_private_key(payload, password=None)
    if not isinstance(key, ed25519.Ed25519PrivateKey):
        raise ValueError("Provided private key is not an Ed25519 key")
    return key


def load_ed25519_public_key(public_key_path: Path) -> object:
    serialization, ed25519, _ = _crypto_modules()
    payload = public_key_path.read_bytes()
    key = serialization.load_pem_public_key(payload)
    if not isinstance(key, ed25519.Ed25519PublicKey):
        raise ValueError("Provided public key is not an Ed25519 key")
    return key


def load_ed25519_public_key_from_pem(public_key_pem: str) -> object:
    serialization, ed25519, _ = _crypto_modules()
    if not isinstance(public_key_pem, str) or not public_key_pem.strip():
        raise ValueError("public_key_pem must be a non-empty string")
    payload = public_key_pem.encode("utf-8")
    key = serialization.load_pem_public_key(payload)
    if not isinstance(key, ed25519.Ed25519PublicKey):
        raise ValueError("Provided public key is not an Ed25519 key")
    return key


def sign_payload(private_key: object, payload: bytes) -> bytes:
    return private_key.sign(payload)


def verify_signature(public_key: object, payload: bytes, signature: bytes) -> bool:
    _, _, exceptions = _crypto_modules()
    try:
        public_key.verify(signature, payload)
        return True
    except exceptions.InvalidSignature:
        return False


def create_detached_signature_artifacts(
    archive_path: Path,
    private_key_path: Path,
    signature_path: Path | None = None,
    metadata_path: Path | None = None,
) -> SignatureArtifactResult:
    if not archive_path.exists() or not archive_path.is_file():
        raise ValueError(f"Archive path '{archive_path}' does not exist")

    if not private_key_path.exists() or not private_key_path.is_file():
        raise ValueError(f"Signing key path '{private_key_path}' does not exist")

    signature_target = signature_path or Path(f"{archive_path}.sig")
    metadata_target = metadata_path or Path(f"{archive_path}.sig.json")

    private_key = load_ed25519_private_key(private_key_path)
    public_key = private_key.public_key()

    archive_payload = archive_path.read_bytes()
    archive_sha256 = _sha256_file(archive_path)
    signature = sign_payload(private_key, archive_payload)

    signature_target.parent.mkdir(parents=True, exist_ok=True)
    signature_target.write_bytes(signature)

    public_key_pem_value = public_key_pem(public_key)

    metadata_payload = {
        "schema_version": 1,
        "algorithm": "ed25519",
        "archive_filename": archive_path.name,
        "archive_sha256": archive_sha256,
        "signature_filename": signature_target.name,
        "signature_base64": base64.b64encode(signature).decode("ascii"),
        "public_key_fingerprint_sha256": public_key_fingerprint(public_key),
        "public_key_pem": public_key_pem_value,
        "verification_hint": "Verify archive authenticity using the publisher public key.",
    }
    metadata_target.parent.mkdir(parents=True, exist_ok=True)
    metadata_target.write_text(
        json.dumps(metadata_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return SignatureArtifactResult(
        signature_path=signature_target,
        metadata_path=metadata_target,
        public_key_fingerprint=metadata_payload["public_key_fingerprint_sha256"],
        archive_sha256=archive_sha256,
    )


def verify_detached_signature_artifacts(
    archive_path: Path,
    signature_path: Path,
    metadata_path: Path,
    expected_public_key_pem: str | None = None,
) -> None:
    if not archive_path.exists() or not archive_path.is_file():
        raise ValueError(f"Archive path '{archive_path}' does not exist")
    if not signature_path.exists() or not signature_path.is_file():
        raise ValueError(f"Signature artifact '{signature_path}' does not exist")
    if not metadata_path.exists() or not metadata_path.is_file():
        raise ValueError(f"Signature metadata '{metadata_path}' does not exist")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Failed to parse signature metadata JSON: {error}")

    if not isinstance(metadata, dict):
        raise ValueError("Signature metadata must be a JSON object")

    if metadata.get("algorithm") != "ed25519":
        raise ValueError("Unsupported signature algorithm in metadata")

    archive_filename = metadata.get("archive_filename")
    if archive_filename != archive_path.name:
        raise ValueError("Signature metadata archive filename does not match install target")

    signature_filename = metadata.get("signature_filename")
    if signature_filename != signature_path.name:
        raise ValueError("Signature metadata signature filename does not match artifact")

    recorded_archive_sha256 = metadata.get("archive_sha256")
    actual_archive_sha256 = _sha256_file(archive_path)
    if recorded_archive_sha256 != actual_archive_sha256:
        raise ValueError("Signature metadata archive checksum does not match archive payload")

    signature_bytes = signature_path.read_bytes()
    metadata_signature_base64 = metadata.get("signature_base64")
    if not isinstance(metadata_signature_base64, str) or not metadata_signature_base64.strip():
        raise ValueError("Signature metadata must include non-empty signature_base64")

    try:
        metadata_signature_bytes = base64.b64decode(metadata_signature_base64.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise ValueError(f"Signature metadata signature_base64 is invalid: {error}")

    if metadata_signature_bytes != signature_bytes:
        raise ValueError("Signature metadata does not match detached signature artifact")

    public_key_pem = metadata.get("public_key_pem")
    if expected_public_key_pem is not None:
        if not isinstance(public_key_pem, str) or public_key_pem.strip() != expected_public_key_pem.strip():
            raise ValueError("Signature metadata public key does not match registry publisher key association")
    signing_public_key = load_ed25519_public_key_from_pem(public_key_pem)
    archive_payload = archive_path.read_bytes()
    if not verify_signature(signing_public_key, archive_payload, signature_bytes):
        raise ValueError("Detached signature verification failed for archive payload")
