"""Tests for the match-database layer and MatchResult contract shape."""

from evolve import MatchResult, load_db, record, save_db


def test_load_missing_db_returns_empty(tmp_path):
    db = load_db(tmp_path / "nope.json")
    assert db == {"matches": [], "versions": {}}


def test_save_then_load_roundtrip(tmp_path):
    path = tmp_path / "m.json"
    db = {"matches": [{"a": "v2", "b": "v1", "wins_a": 3, "wins_b": 1}],
          "versions": {"v1": {}, "v2": {}}}
    save_db(db, path)
    assert load_db(path) == db


def test_record_appends_and_registers_versions():
    db = {"matches": [], "versions": {}}
    record(db, MatchResult(a="v2", b="v1", wins_a=7, wins_b=3))
    assert len(db["matches"]) == 1
    assert set(db["versions"]) == {"v1", "v2"}


def test_to_dict_omits_optional_fields_when_absent():
    d = MatchResult(a="v2", b="v1", wins_a=7, wins_b=3).to_dict()
    assert d == {"a": "v2", "b": "v1", "wins_a": 7, "wins_b": 3}
    assert "draws" not in d  # zero draws are not serialized
    assert "note" not in d


def test_to_dict_includes_set_fields():
    d = MatchResult(
        a="v2", b="v1", wins_a=7, wins_b=3, draws=2, mean_a=3.0, mean_b=2.0, note="x"
    ).to_dict()
    assert d == {
        "a": "v2", "b": "v1", "wins_a": 7, "wins_b": 3,
        "draws": 2, "mean_a": 3.0, "mean_b": 2.0, "note": "x",
    }
