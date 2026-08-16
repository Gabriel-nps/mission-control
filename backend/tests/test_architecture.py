"""Static analysis verification of Clean Architecture layer boundaries.

Validates: Requirements 6.1, 6.2, 6.3, 6.8

These tests walk the source tree with the `ast` module and inspect every
import statement, so they catch violations regardless of formatting,
line breaks, or aliasing (which a grep-based check would miss).
"""

import ast
from pathlib import Path
from typing import Iterator, List, Tuple

APP_ROOT = Path(__file__).resolve().parent.parent / "app"
DOMAIN_ROOT = APP_ROOT / "domain"
APPLICATION_ROOT = APP_ROOT / "application"

# Modules the inner layers must never depend on.
FORBIDDEN_FOR_APPLICATION = ("app.infrastructure", "app.presentation")
FORBIDDEN_FRAMEWORKS = (
    "fastapi",
    "starlette",
    "kafka",
    "confluent_kafka",
    "jwt",
)


def _python_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _imported_modules(path: Path) -> List[Tuple[str, int]]:
    """Return (module_name, lineno) for every import in the file.

    Relative imports are resolved to their absolute dotted package name so
    that `from ...infrastructure import x` is detected as well.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    try:
        package_parts = path.relative_to(APP_ROOT.parent).with_suffix("").parts
    except ValueError:  # file outside the app tree (e.g. a temp fixture)
        package_parts = (path.stem,)
    if path.name == "__init__.py":
        package_parts = package_parts[:-1]

    modules: List[Tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append((alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                base = node.module or ""
            else:
                # `from . import x` -> current package; level 2 -> parent, etc.
                anchor = package_parts[: len(package_parts) - (node.level - 1)]
                base = ".".join([*anchor, node.module] if node.module else anchor)
            modules.append((base, node.lineno))
            for alias in node.names:
                modules.append((f"{base}.{alias.name}" if base else alias.name, node.lineno))
    return modules


def _matches(module: str, forbidden: str) -> bool:
    """True when `module` is `forbidden` or a submodule of it."""
    return module == forbidden or module.startswith(forbidden + ".")


def _violations(root: Path, forbidden: Tuple[str, ...]) -> List[str]:
    found: List[str] = []
    for path in _python_files(root):
        for module, lineno in _imported_modules(path):
            for name in forbidden:
                if _matches(module, name):
                    rel = path.relative_to(APP_ROOT.parent)
                    found.append(f"{rel}:{lineno} imports '{module}'")
    return found


def test_source_roots_exist_and_are_non_empty() -> None:
    """Guard against the checks silently passing on an empty tree."""
    assert DOMAIN_ROOT.is_dir(), f"missing {DOMAIN_ROOT}"
    assert APPLICATION_ROOT.is_dir(), f"missing {APPLICATION_ROOT}"
    assert any(p.name != "__init__.py" for p in _python_files(DOMAIN_ROOT))
    assert any(p.name != "__init__.py" for p in _python_files(APPLICATION_ROOT))


def test_application_layer_has_no_infrastructure_or_presentation_imports() -> None:
    """Requirements 6.1, 6.2, 6.3: application depends only on inner layers."""
    violations = _violations(APPLICATION_ROOT, FORBIDDEN_FOR_APPLICATION)
    assert not violations, "Application layer must not import outer layers:\n" + "\n".join(
        violations
    )


def test_domain_layer_has_no_infrastructure_or_presentation_imports() -> None:
    """Requirement 6.8: domain is independent of outer layers."""
    violations = _violations(DOMAIN_ROOT, FORBIDDEN_FOR_APPLICATION)
    assert not violations, "Domain layer must not import outer layers:\n" + "\n".join(violations)


def test_domain_layer_has_no_framework_imports() -> None:
    """Requirement 6.8: no FastAPI, Kafka, or JWT imports in domain."""
    violations = _violations(DOMAIN_ROOT, FORBIDDEN_FRAMEWORKS)
    assert not violations, "Domain layer must not import frameworks:\n" + "\n".join(violations)


def test_application_layer_has_no_framework_imports() -> None:
    """Requirement 6.8: no FastAPI, Kafka, or JWT imports in application."""
    violations = _violations(APPLICATION_ROOT, FORBIDDEN_FRAMEWORKS)
    assert not violations, "Application layer must not import frameworks:\n" + "\n".join(
        violations
    )


def test_detector_flags_a_known_violation(tmp_path: Path) -> None:
    """Sanity check: the AST walker actually detects forbidden imports."""
    offender = tmp_path / "offender.py"
    offender.write_text(
        "import jwt\n"
        "from app.infrastructure.kafka.producer import KafkaEventPublisher\n"
        "from fastapi import Depends\n",
        encoding="utf-8",
    )
    modules = [module for module, _ in _imported_modules(offender)]
    assert any(_matches(m, "jwt") for m in modules)
    assert any(_matches(m, "app.infrastructure") for m in modules)
    assert any(_matches(m, "fastapi") for m in modules)
