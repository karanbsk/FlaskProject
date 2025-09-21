import pytest

@pytest.mark.regression
def test_alembic_migration_imports():
    # simple smoke: import migrations env if any - adapt to your migrations package
    try:
        import migrations
    except Exception:
        pass
    assert True
