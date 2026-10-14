"""Kiểm tra tĩnh infra/docker-compose.yml, không cần chạy Docker."""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "infra" / "docker-compose.yml"
ENV_EXAMPLE = ROOT / ".env.example"

SERVICES = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))["services"]


@pytest.mark.parametrize("name", sorted(SERVICES))
def test_service_has_memory_limit(name):
    assert "mem_limit" in SERVICES[name], f"{name} thiếu mem_limit"


@pytest.mark.parametrize("name", sorted(SERVICES))
def test_image_is_pinned(name):
    image = SERVICES[name].get("image", "")
    tag = image.rsplit(":", 1)[-1] if ":" in image else ""
    assert tag and tag != "latest", f"{name}: image '{image}' phải ghi rõ phiên bản"


def test_env_example_declares_every_variable():
    used = set(re.findall(r"\$\{([A-Z0-9_]+)", COMPOSE.read_text(encoding="utf-8")))
    declared = {line.split("=", 1)[0] for line in ENV_EXAMPLE.read_text().splitlines() if "=" in line}
    assert used <= declared, f".env.example thiếu: {sorted(used - declared)}"
