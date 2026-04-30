from __future__ import annotations

from kinnoo.config import RegistryConfig
from kinnoo import list_command, search_command


class _RemoteClientStub:
    def __init__(self, *, base_url: str, token: str, tenant_slug: str) -> None:
        self.base_url = base_url
        self.token = token
        self.tenant_slug = tenant_slug


class _RegistryServiceListStub:
    def __init__(self, backend: object) -> None:
        self.backend = backend

    def list_latest_agents(self) -> list[dict[str, object]]:
        return [
            {
                "name": "dict-remote-agent",
                "latest_version": "1.2.3",
                "description": "dict summary",
                "archive_size_bytes": 512,
            }
        ]


class _RegistryServiceSearchStub:
    def __init__(self, backend: object) -> None:
        self.backend = backend

    def search_agents(self, *, query: str) -> list[dict[str, object]]:
        assert query == "dict"
        return [
            {
                "name": "dict-remote-agent",
                "latest_version": "1.2.3",
                "description": "dict summary",
            }
        ]

    def list_clawhub_mirror_records(self) -> list[dict[str, object]]:
        return []


def test_list_remote_accepts_dict_summaries(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        list_command,
        "load_registry_config",
        lambda: RegistryConfig(
            registry_url="https://registry.example.test",
            registry_token="token",
            tenant_slug="global",
        ),
    )
    monkeypatch.setattr(list_command, "RemoteRegistryClient", _RemoteClientStub)
    monkeypatch.setattr(list_command, "RegistryService", _RegistryServiceListStub)

    exit_code = list_command.list_agents(source="remote")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Remote registry agents:" in captured.out
    assert "dict-remote-agent | latest: 1.2.3 | description: dict summary" in captured.out


def test_search_remote_accepts_dict_summaries(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        search_command,
        "load_registry_config",
        lambda: RegistryConfig(
            registry_url="https://registry.example.test",
            registry_token="token",
            tenant_slug="global",
        ),
    )
    monkeypatch.setattr(search_command, "RemoteRegistryClient", _RemoteClientStub)
    monkeypatch.setattr(search_command, "RegistryService", _RegistryServiceSearchStub)

    exit_code = search_command.search_agents(query="dict", source="remote")
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Remote registry search results for: dict" in captured.out
    assert "dict-remote-agent | latest: 1.2.3 | description: dict summary" in captured.out
