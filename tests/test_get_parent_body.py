from inspect import currentframe
from correction_helper import get_parent_body


class GetMyCode:
    def __init__(self, *args, **kwargs):
        self.source = get_parent_body()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        pass


def test_single_line():
    with GetMyCode() as code:
        print(test_single_line)
    assert code.source == "print(test_single_line)"


def test_multiline():
    some = 1
    dummy = 2
    lines = 3
    with GetMyCode() as code:
        a = 5
        b = a
        print(a, b)
    assert code.source == "a = 5\nb = a\nprint(a, b)"


def test_args_indented():
    some = 1
    dummy = 2
    lines = 3
    with GetMyCode(
        with_some_extra_long_args=0, yes_i_know_its_not_java_but_yet=1
    ) as code:
        a = 5
        b = a
        print(a, b)
    assert code.source == "a = 5\nb = a\nprint(a, b)"


def test_args_indented_under_an_if():
    some = 1
    dummy = 2
    lines = 3
    if some == dummy - 1:
        with GetMyCode(
            with_some_extra_long_args=0, yes_i_know_its_not_java_but_yet=1
        ) as code:
            a = 5
            b = a
    assert code.source == "a = 5\nb = a"
