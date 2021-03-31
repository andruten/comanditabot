from commands import MiMiMiCommandHandler


def test_mimimi():
    text = "Hola"
    response = MiMiMiCommandHandler().do_mimimi(text)
    assert response == "Hili"


def test_mimimi_special_chars():
    text = "AÁÀÄÂ"
    response = MiMiMiCommandHandler().do_mimimi(text)
    assert response == "IÍÌÏÎ"
