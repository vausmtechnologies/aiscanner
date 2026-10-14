from parser.text_cleaner import clean_text


def test_clean_text_normalizes_content() -> None:
    raw = "Vehicle# Number:\tMH-12 AB 1234\n\nEngine Number!!!"
    cleaned = clean_text(raw)
    assert cleaned == "vehicle number mh 12 ab 1234 engine number"


def test_clean_text_handles_empty_input() -> None:
    assert clean_text("") == ""
