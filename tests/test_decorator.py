import pytest
from correction_helper import student_code


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
    assert "Your code printed" in err
    assert "Coucou" in err
    assert not out


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


def test_student_code_expect(capsys):
    with pytest.raises(SystemExit):
        with student_code(print_allowed=False, print_expect="Coucou"):
            print("Coucou")
    out, err = capsys.readouterr()
    assert "Coucou" in err
    assert "printed what I expected" in err
    assert not out
