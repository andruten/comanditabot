from pathlib import Path

import pytest

from persistence import ResilientPicklePersistence

STATE = {
    "user_data": {1: {"mimimi": "aáàäâ"}},
    "chat_data": {42: {"flags": {"reactions": True}}},
    "conversations": {"mimimi": {}},
    "bot_data": {"mark": "of-cain"},
}
EMPTY_KEYS = ("user_data", "chat_data", "conversations", "bot_data")


def make_persistence(filepath: Path) -> ResilientPicklePersistence:
    persistence = ResilientPicklePersistence(filepath=filepath, update_interval=0)
    for key, value in STATE.items():
        setattr(persistence, key, value)
    persistence.callback_data = None
    return persistence


def write_state(filepath: Path) -> None:
    make_persistence(filepath)._dump_singlefile()


def read_state(filepath: Path) -> dict:
    persistence = ResilientPicklePersistence(filepath=filepath, update_interval=0)
    persistence._load_singlefile()
    return {
        "user_data": persistence.user_data,
        "conversations": persistence.conversations,
    }


@pytest.fixture
def filepath(tmp_path: Path) -> Path:
    return tmp_path / "bot_state.pickle"


def test_first_dump_writes_the_state_without_a_backup(filepath: Path) -> None:
    backup_path = filepath.with_name(filepath.name + ".bak")

    write_state(filepath)

    assert filepath.is_file()
    assert not backup_path.is_file()


def test_dump_keeps_a_backup_of_the_previous_state(filepath: Path) -> None:
    write_state(filepath)
    backup_path = filepath.with_name(filepath.name + ".bak")

    persistence = make_persistence(filepath)
    persistence.conversations = {"changed": True}
    persistence._dump_singlefile()

    assert read_state(backup_path)["conversations"] == {"mimimi": {}}
    assert read_state(filepath)["conversations"] == {"changed": True}


def test_load_recovers_the_last_backup_from_a_corrupted_file(filepath: Path) -> None:
    write_state(filepath)
    write_state(filepath)
    backup_path = filepath.with_name(filepath.name + ".bak")
    assert backup_path.is_file()

    filepath.write_bytes(b"this is not a pickle")
    persistence = make_persistence(filepath)
    persistence._load_singlefile()

    assert persistence.user_data == STATE["user_data"]
    assert persistence.bot_data == STATE["bot_data"]
    assert persistence.conversations == STATE["conversations"]
    assert filepath.with_name(filepath.name + ".corrupt").is_file()


def test_load_starts_with_an_empty_state_without_a_backup(filepath: Path) -> None:
    filepath.write_bytes(b"this is not a pickle")

    persistence = make_persistence(filepath)
    persistence._load_singlefile()

    for key in EMPTY_KEYS:
        assert getattr(persistence, key) == {}
    assert persistence.callback_data is None


def test_load_falls_back_to_empty_state_when_the_backup_is_corrupt(
    filepath: Path,
) -> None:
    write_state(filepath)
    write_state(filepath)
    backup_path = filepath.with_name(filepath.name + ".bak")
    backup_path.write_bytes(b"this is not a pickle")
    filepath.write_bytes(b"this is not a pickle either")

    persistence = make_persistence(filepath)
    persistence._load_singlefile()

    for key in EMPTY_KEYS:
        assert getattr(persistence, key) == {}
