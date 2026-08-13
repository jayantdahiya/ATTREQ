"""Protect the architecture-specific PyTorch pins used by the API image."""

from pathlib import Path

from packaging.requirements import Requirement


def _torch_requirements() -> list[Requirement]:
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    return [
        Requirement(line.split("#", 1)[0].strip())
        for line in requirements.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("torch")
    ]


def _selected_versions(machine: str) -> list[str]:
    environment = {
        "platform_system": "Linux",
        "platform_machine": machine,
    }
    return [
        str(requirement.specifier)
        for requirement in _torch_requirements()
        if requirement.marker is None or requirement.marker.evaluate(environment)
    ]


def test_linux_x86_64_uses_explicit_cpu_wheel() -> None:
    assert _selected_versions("x86_64") == ["==2.2.2+cpu"]


def test_linux_aarch64_uses_available_arm64_wheel() -> None:
    assert _selected_versions("aarch64") == ["==2.2.2"]


def test_numpy_stays_on_torch_22_compatible_abi() -> None:
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    numpy_line = next(
        line.split("#", 1)[0].strip()
        for line in requirements.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("numpy")
    )
    assert Requirement(numpy_line).specifier.contains("1.26.4")
    assert not Requirement(numpy_line).specifier.contains("2.0.0")
