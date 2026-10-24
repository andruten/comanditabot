import pytest

import comandita


def test_main_exits_without_a_bot_token(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)

    with pytest.raises(SystemExit) as error:
        comandita.main()

    assert "BOT_TOKEN" in str(error.value)
