"""Test that all modules define explicit public APIs"""
import importlib
import pkgutil
from pathlib import Path


def test_all_modules_have_explicit_exports():
    """Test that all modules define __all__"""
    src_dir = Path(__file__).parent.parent / "src" / "cenv"

    modules_without_all = []

    for module_info in pkgutil.iter_modules([str(src_dir)]):
        if module_info.name == "__init__":
            continue

        module = importlib.import_module(f"cenv.{module_info.name}")

        if not hasattr(module, "__all__"):
            modules_without_all.append(module_info.name)

    assert not modules_without_all, (
        f"Modules without __all__: {', '.join(modules_without_all)}\n"
        f"All public modules must define __all__ for explicit API"
    )


def test_all_exports_are_valid():
    """Test that __all__ only lists items that exist"""
    src_dir = Path(__file__).parent.parent / "src" / "cenv"

    errors = []

    for module_info in pkgutil.iter_modules([str(src_dir)]):
        if module_info.name == "__init__":
            continue

        module = importlib.import_module(f"cenv.{module_info.name}")

        if hasattr(module, "__all__"):
            for name in module.__all__:
                if not hasattr(module, name):
                    errors.append(f"{module_info.name}.__all__ lists '{name}' but it doesn't exist")

    assert not errors, "\n".join(errors)
