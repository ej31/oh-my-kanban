"""Provider registry tests."""

from oh_my_kanban.core.provider_registry import iter_provider_specs


def test_provider_registry_contains_plane_and_linear() -> None:
    """Provider registry는 plane과 linear를 모두 등록해야 한다."""

    specs = {spec.name: spec for spec in iter_provider_specs()}
    assert "plane" in specs
    assert "linear" in specs
    assert specs["plane"].aliases == ("pl",)
    assert specs["linear"].aliases == ("ln",)
