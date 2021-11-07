import pytest
from correction_helper import student_code, code


def test_student_code(capsys):
    with pytest.raises(SystemExit):
        with student_code():
            raise ValueError("Pouette")
    out, err = capsys.readouterr()
    assert "Pouette" in err
    assert "Traceback" in err
    assert not out


def test_not_die_on_no_exception():
    with student_code(print_allowed=True) as run:
        print("Coucou")
    assert run.out == "Coucou"


def test_student_code_no_print(capsys):
    with pytest.raises(SystemExit):
        with student_code(print_allowed=False) as run:
            print("Coucou")
    assert run.out == "Coucou"
    out, err = capsys.readouterr()
    assert "Your code printed" in out
    assert "Coucou" in out
    assert not err


def test_not_die_on_no_print(capsys):
    with student_code() as run:
        pass
    out, err = capsys.readouterr()
    assert not err
    assert not out
    assert not run.out
    assert not run.err


def test_student_code_during_print_check(capsys):
    with pytest.raises(SystemExit):
        with student_code(print_allowed=False):
            raise ValueError("Pouette")
    out, err = capsys.readouterr()
    assert "Pouette" in err
    assert "ValueError" in err
    assert not out


def test_student_code_print_passthrue(capsys):
    with student_code(print_allowed=True, print_prefix="Your code printed:"):
        print("Hello world")
    out, err = capsys.readouterr()
    assert (
        out
        == """Your code printed:

    :::text
    Hello world
"""
    )
    assert not err


def test_student_code_print_prefix_as_list_or_paragraphs(capsys):
    with student_code(
        print_allowed=True,
        print_prefix=[
            "Your function, called as:",
            code("example(call)", "python"),
            "printed:",
        ],
    ):
        print("Hello world")
    out, err = capsys.readouterr()
    assert (
        out
        == """Your function, called as:

    :::python
    example(call)

printed:

    :::text
    Hello world
"""
    )
    assert not err
