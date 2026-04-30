from __future__ import annotations


NODEJS_COMPATIBLE_LANGUAGES: set[str] = {"nodejs", "javascript", "typescript", "js", "ts"}


def normalize_runtime_language(language: str | None, *, default: str = "python") -> str:
    if language is None:
        return default
    normalized = language.strip().lower()
    return normalized or default


def is_nodejs_compatible_runtime(language: str | None) -> bool:
    normalized = normalize_runtime_language(language)
    return normalized in NODEJS_COMPATIBLE_LANGUAGES
