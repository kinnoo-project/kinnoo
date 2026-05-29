from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform
import sys


@dataclass(frozen=True)
class BinaryInspection:
    """Inspection summary for executable artifact compatibility checks."""

    format_name: str
    target_os: str
    target_arches: tuple[str, ...]


_ELF_MACHINE_TO_GOARCH = {
    0x03: "386",
    0x28: "arm",
    0x3E: "amd64",
    0xB7: "arm64",
}

_PE_MACHINE_TO_GOARCH = {
    0x014C: "386",
    0x01C0: "arm",
    0x01C4: "arm",
    0x8664: "amd64",
    0xAA64: "arm64",
}

_MACH_CPU_TO_GOARCH = {
    7: "386",
    12: "arm",
    0x01000007: "amd64",
    0x0100000C: "arm64",
}


def resolve_host_go_platform() -> tuple[str, str]:
    """Return host platform values normalized to GOOS/GOARCH labels."""

    if sys.platform.startswith("linux"):
        goos = "linux"
    elif sys.platform == "darwin":
        goos = "darwin"
    elif sys.platform.startswith("win"):
        goos = "windows"
    else:
        goos = sys.platform

    machine = platform.machine().strip().lower()
    goarch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
        "armv8": "arm64",
        "armv7": "arm",
        "armv7l": "arm",
        "armv6": "arm",
        "armv6l": "arm",
        "i386": "386",
        "i686": "386",
        "x86": "386",
    }
    goarch = goarch_map.get(machine, machine)
    return goos, goarch


def _read_file_slice(binary_path: Path, offset: int, length: int) -> bytes:
    with binary_path.open("rb") as binary_file:
        binary_file.seek(offset)
        return binary_file.read(length)


def _deduplicate(values: list[str]) -> tuple[str, ...]:
    ordered: list[str] = []
    for value in values:
        if value and value not in ordered:
            ordered.append(value)
    return tuple(ordered)


def _normalize_mach_cputype(cputype: int) -> int:
    if cputype in _MACH_CPU_TO_GOARCH:
        return cputype

    base_type = cputype & 0x00FFFFFF
    abi64_flag = bool(cputype & 0x01000000)
    if base_type == 7 and abi64_flag:
        return 0x01000007
    if base_type == 12 and abi64_flag:
        return 0x0100000C
    return base_type


def _inspect_elf(binary_path: Path, header: bytes) -> tuple[BinaryInspection | None, str | None]:
    if len(header) < 20:
        return None, "ELF header is truncated"

    elf_data_encoding = header[5]
    if elf_data_encoding == 1:
        endian = "little"
    elif elf_data_encoding == 2:
        endian = "big"
    else:
        return None, "ELF header has unsupported byte-order marker"

    machine = int.from_bytes(header[18:20], endian)
    goarch = _ELF_MACHINE_TO_GOARCH.get(machine)
    target_arches = (goarch,) if goarch is not None else ()
    return BinaryInspection(format_name="ELF", target_os="linux", target_arches=target_arches), None


def _inspect_pe(binary_path: Path, header: bytes) -> tuple[BinaryInspection | None, str | None]:
    if len(header) < 64:
        return None, "PE header is truncated"

    pe_offset = int.from_bytes(header[0x3C:0x40], "little")
    signature_and_machine = _read_file_slice(binary_path, pe_offset, 6)
    if len(signature_and_machine) < 6 or signature_and_machine[:4] != b"PE\x00\x00":
        return None, "PE signature is missing or invalid"

    machine = int.from_bytes(signature_and_machine[4:6], "little")
    goarch = _PE_MACHINE_TO_GOARCH.get(machine)
    target_arches = (goarch,) if goarch is not None else ()
    return BinaryInspection(format_name="PE", target_os="windows", target_arches=target_arches), None


def _inspect_mach_o(binary_path: Path, header: bytes) -> tuple[BinaryInspection | None, str | None]:
    if len(header) < 8:
        return None, "Mach-O header is truncated"

    magic = header[:4]
    thin_magics = {
        b"\xFE\xED\xFA\xCE": "big",
        b"\xFE\xED\xFA\xCF": "big",
        b"\xCE\xFA\xED\xFE": "little",
        b"\xCF\xFA\xED\xFE": "little",
    }
    fat_magics = {
        b"\xCA\xFE\xBA\xBE": ("big", False),
        b"\xBE\xBA\xFE\xCA": ("little", False),
        b"\xCA\xFE\xBA\xBF": ("big", True),
        b"\xBF\xBA\xFE\xCA": ("little", True),
    }

    thin_endian = thin_magics.get(magic)
    if thin_endian is not None:
        cputype = int.from_bytes(header[4:8], thin_endian, signed=True)
        normalized_cputype = _normalize_mach_cputype(cputype)
        goarch = _MACH_CPU_TO_GOARCH.get(normalized_cputype)
        target_arches = (goarch,) if goarch is not None else ()
        return BinaryInspection(format_name="Mach-O", target_os="darwin", target_arches=target_arches), None

    fat_info = fat_magics.get(magic)
    if fat_info is None:
        return None, "Mach-O magic value is unsupported"

    fat_endian, uses_64bit_arch_records = fat_info
    arch_record_size = 32 if uses_64bit_arch_records else 20
    architecture_count = int.from_bytes(header[4:8], fat_endian)
    architecture_count = min(architecture_count, 16)
    if architecture_count <= 0:
        return BinaryInspection(format_name="Mach-O", target_os="darwin", target_arches=()), None

    raw_arch_records = _read_file_slice(binary_path, 8, architecture_count * arch_record_size)
    if len(raw_arch_records) < arch_record_size:
        return None, "Mach-O fat header is truncated"

    discovered_arches: list[str] = []
    for index in range(architecture_count):
        start = index * arch_record_size
        stop = start + arch_record_size
        arch_record = raw_arch_records[start:stop]
        if len(arch_record) < 4:
            break

        cputype = int.from_bytes(arch_record[:4], fat_endian, signed=True)
        normalized_cputype = _normalize_mach_cputype(cputype)
        goarch = _MACH_CPU_TO_GOARCH.get(normalized_cputype)
        if goarch is not None:
            discovered_arches.append(goarch)

    return BinaryInspection(
        format_name="Mach-O",
        target_os="darwin",
        target_arches=_deduplicate(discovered_arches),
    ), None


def inspect_binary_artifact(binary_path: Path) -> tuple[BinaryInspection | None, str | None]:
    """Inspect executable header metadata for format and target platform hints."""

    if not binary_path.exists():
        return None, f"entrypoint file not found: {binary_path}"
    if not binary_path.is_file():
        return None, f"entrypoint path is not a file: {binary_path}"

    try:
        header = _read_file_slice(binary_path, 0, 4096)
    except OSError as error:
        return None, f"could not read binary header from '{binary_path}': {error}"

    if len(header) < 4:
        return None, "binary header is too short"

    if header.startswith(b"\x7FELF"):
        return _inspect_elf(binary_path, header)

    if header.startswith(b"MZ"):
        return _inspect_pe(binary_path, header)

    mach_magic_prefixes = {
        b"\xFE\xED\xFA\xCE",
        b"\xFE\xED\xFA\xCF",
        b"\xCE\xFA\xED\xFE",
        b"\xCF\xFA\xED\xFE",
        b"\xCA\xFE\xBA\xBE",
        b"\xBE\xBA\xFE\xCA",
        b"\xCA\xFE\xBA\xBF",
        b"\xBF\xBA\xFE\xCA",
    }
    if header[:4] in mach_magic_prefixes:
        return _inspect_mach_o(binary_path, header)

    return None, "unsupported executable format (expected Mach-O, ELF, or PE header)"
