import pytest
from hypothesis import given
from hypothesis.strategies import text
from correction_helper import compare


@given(text())
def test_equals(text):
    assert compare(text, text) is None  # Does nothing when there's no diff


def test_differ():
    with pytest.raises(SystemExit):
        compare("a", "b")


def test_mine_longer(capsys):
    with pytest.raises(SystemExit):
        compare("a\nb", "a")
    out, err = capsys.readouterr()
    assert "a" in err
    assert "b" in err


def test_their_longer(capsys):
    with pytest.raises(SystemExit):
        compare("a", "a\nb")
    out, err = capsys.readouterr()
    assert "a" in err
    assert "b" in err
