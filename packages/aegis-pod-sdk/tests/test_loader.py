import pytest

from aegis_pod_sdk import resolve_entrypoint


def test_resolves_module_level_function():
    fn = resolve_entrypoint("aegis_pod_sdk.util.sha256_upper")
    assert fn("abc") == __import__("aegis_pod_sdk").sha256_upper("abc")


def test_resolves_class_then_nested_attribute():
    cls = resolve_entrypoint("aegis_pod_sdk.tensors.TensorKind")
    from aegis_pod_sdk import TensorKind
    assert cls is TensorKind


def test_resolves_class_method_attribute_chain():
    member = resolve_entrypoint("aegis_pod_sdk.tensors.TensorKind.SPINE")
    from aegis_pod_sdk import TensorKind
    assert member == TensorKind.SPINE


def test_raises_on_unimportable_path():
    with pytest.raises(ImportError):
        resolve_entrypoint("nonexistent_package_xyz.module.Thing")


def test_raises_on_missing_attribute():
    with pytest.raises(AttributeError):
        resolve_entrypoint("aegis_pod_sdk.util.NoSuchThing")


def test_raises_on_path_without_dot():
    with pytest.raises(ValueError):
        resolve_entrypoint("nodothere")
