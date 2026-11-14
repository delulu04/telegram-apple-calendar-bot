from calendar_tags import extract_tag, match_calendar

NAMES = ["DELS", "BDAY", "REMINDERS", "SCHOOL", "EXTRA SCHOOL", "TUITION",
         "WORKOUT", "IMPORTANT", "WORK", "✨ delulu plans"]


def test_extract_tag_end():
    assert extract_tag("Tutorial thurs 10-12pm #school") == ("Tutorial thurs 10-12pm", "school")


def test_extract_tag_start_and_middle():
    assert extract_tag("#workout gym tmr 7am") == ("gym tmr 7am", "workout")
    assert extract_tag("gym #workout tmr 7am") == ("gym tmr 7am", "workout")


def test_extract_no_tag():
    assert extract_tag("dinner w ash fri 7pm") == ("dinner w ash fri 7pm", None)


def test_extract_multiword_tag_with_dash_or_underscore():
    assert extract_tag("chem tut mon 4pm #extra-school")[1] == "extra-school"
    assert extract_tag("chem tut mon 4pm #extra_school")[1] == "extra_school"


def test_hash_inside_word_is_not_a_tag():
    assert extract_tag("CS#2 lab tmr 2pm") == ("CS#2 lab tmr 2pm", None)


def test_exact_match_case_insensitive():
    assert match_calendar("school", NAMES) == "SCHOOL"
    assert match_calendar("WORK", NAMES) == "WORK"  # exact beats prefix of WORKOUT


def test_multiword_names():
    assert match_calendar("extra-school", NAMES) == "EXTRA SCHOOL"
    assert match_calendar("extraschool", NAMES) == "EXTRA SCHOOL"
    assert match_calendar("extra", NAMES) == "EXTRA SCHOOL"


def test_prefix_match():
    assert match_calendar("sch", NAMES) == "SCHOOL"
    assert match_calendar("bd", NAMES) == "BDAY"
    assert match_calendar("tu", NAMES) == "TUITION"


def test_ambiguous_prefix_returns_none():
    assert match_calendar("wo", NAMES) is None  # WORK / WORKOUT


def test_emoji_name():
    assert match_calendar("delulu", NAMES) == "✨ delulu plans"


def test_no_match():
    assert match_calendar("netflix", NAMES) is None
    assert match_calendar("", NAMES) is None
