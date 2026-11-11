from reactions.history import ChatHistory, chat_history


def test_recent_returns_messages_in_chronological_order():
    history = ChatHistory()
    history.add(1, "primero")
    history.add(1, "segundo")

    assert history.recent(1) == ["primero", "segundo"]


def test_unknown_chat_returns_empty_list():
    assert ChatHistory().recent(42) == []


def test_history_is_bounded_per_chat():
    history = ChatHistory()
    cap = ChatHistory.MAX_MESSAGES_PER_CHAT
    for index in range(cap + 5):
        history.add(1, f"mensaje {index}")

    assert len(history.recent(1)) == cap
    assert history.recent(1)[0] == f"mensaje {5}"


def test_recent_returns_only_the_last_messages_when_a_limit_is_given():
    history = ChatHistory()
    for index in range(5):
        history.add(1, f"mensaje {index}")

    assert history.recent(1, limit=2) == ["mensaje 3", "mensaje 4"]


def test_chats_are_isolated():
    history = ChatHistory()
    history.add(1, "del chat 1")
    history.add(2, "del chat 2")

    assert history.recent(1) == ["del chat 1"]
    assert history.recent(2) == ["del chat 2"]


def test_empty_texts_are_ignored():
    history = ChatHistory()
    history.add(1, "")
    history.add(1, "hola")

    assert history.recent(1) == ["hola"]


def test_clear_forgets_the_chat():
    history = ChatHistory()
    history.add(1, "hola")
    history.clear(1)

    assert history.recent(1) == []


def test_module_exposes_a_shared_chat_history():
    assert isinstance(chat_history, ChatHistory)
