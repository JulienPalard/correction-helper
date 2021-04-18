from io import StringIO
import random
from pathlib import Path
import sys
import gettext
import os
import signal
from itertools import zip_longest
from traceback import format_exc
from contextlib import redirect_stdout, redirect_stderr
from textwrap import indent
from contextlib import contextmanager
import subprocess
import shlex

import friendly_traceback
from friendly_traceback import exclude_file_from_traceback

friendly_traceback.set_lang(os.environ.get("LANGUAGE", "en"))

exclude_file_from_traceback(__file__)

_ = gettext.translation("check", Path(__file__).parent, fallback=True).gettext


def code(text, language="text"):
    return "    :::" + language + "\n" + indent(str(text), "    ")


def stderr(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def fail(*args, sep="\n\n"):
    """Print args on stderror and exit with failure (code=1).

    By default, if multiple args are given, they are separated by two
    newlines, usefull to build Markdown paragraphs.
    """
    stderr(sep.join(args))
    sys.exit(1)


def congrats():
    """Generates a generic congratulation sentence."""
    return random.choice(
        [
            "Congrats! Your exercise is OK.",
            "Nice job! Right answer.",
            "Well done! Correct answer.",
            "Spot on! Looks good to me!",
            "Bravo!! Your answer is correct.",
            "Good!! Correct answer.",
        ]
    )


def _handle_student_exception(prefix, friendly=False):
    if friendly:
        friendly_traceback.explain_traceback()
    else:
        if prefix:
            stderr(prefix, end="\n\n")
        stderr(code("".join(format_exc()), "pytb"))
    sys.exit(1)


class Tee(StringIO):
    """Like tee. (man tee), combining a StringIO and a normal file."""

    def __init__(self, twin, **kwargs):
        self.twin = twin
        super().__init__(**kwargs)

    def write(self, s):
        self.twin.write(indent(s, "    "))
        super().write(s)


class Run:
    def __init__(self, stdout, stderr):
        self.stdout = stdout
        self.stderr = stderr

    @property
    def out(self):
        return self.stdout.getvalue().strip()

    @property
    def err(self):
        return self.stderr.getvalue().strip()


class TimeoutError(Exception):
    pass


@contextmanager
def deadline(timeout=1):
    def handler(signum, frame):
        raise TimeoutError

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    yield
    signal.alarm(0)


@contextmanager
def student_code(
    exception_prefix="Got an exception:",
    friendly=True,
    print_allowed=False,
    print_prefix="Your code printed something (it should **not**):",
    print_expect=None,
    print_expect_message="""Your code printed what I expected it to return,
so maybe just replace your `print` call by a `return` statement.""",
    too_slow_message="Your program looks too slow, looks like an infinite loop.",
    timeout=1,
):
    """Decorator usefull to run student code.

    It help them spot common errors like:
    - using `input()`
    - using `exit()`
    - raising an exception (pretty printing it in Markdown)

    print_allowed can take 3 values:
    - False: Exercise fails with print_prefix if the student prints.
    - None: prints are allowed, captured, and passed to stdout/stderr.
    - True: prints are allowed, captured, but not passed to stdout/stderr.

    Use as:
    with student_code() as run:
        their_value = their_function(your_argument)
    print(run.out, run.err)  # You have access to what they tried to write
                             # to stdout and stderr (both stripped).
    """
    old_stdin = sys.stdin
    if print_allowed is None:
        run = Run(Tee(sys.stdout), Tee(sys.stderr))
    else:
        run = Run(StringIO(), StringIO())
    try:
        sys.stdin = None
        with redirect_stdout(run.stdout):
            with redirect_stderr(run.stderr):
                with deadline(timeout):
                    yield run
    except TimeoutError:
        fail(too_slow_message)
    except SystemExit:
        fail(
            """Your program tried to exit,
remove any `exit()` or `sys.exit()` from your code,
else I won't be able to check it."""
        )
    except RuntimeError as err:
        if "lost sys.stdin" not in str(err):
            _handle_student_exception(exception_prefix, friendly)
        fail("Don't use the `input` builtin, there's no human to interact with here.")
    except:  # noqa
        _handle_student_exception(exception_prefix, friendly)
    finally:
        sys.stdin = old_stdin
    if print_allowed is False:
        if run.err or run.out:
            stderr(print_prefix, end="\n\n")
            if run.err:
                stderr(code(run.err, language="text"))
            if run.out:
                stderr(code(run.out, language="text"))
            if print_expect and run.out == print_expect:
                stderr(print_expect_message, end="\n\n")
            sys.exit(1)


class Section:
    def __init__(self, name, prefix="", suffix="", highlight=""):
        self.name = name
        self.prefix = prefix
        self.suffix = suffix
        self.highlight = highlight


MARKDOWN_ITEMS = [
    Section("header", prefix="## "),
    Section("simulated_python_traceback", highlight="pytb"),
    Section("suggest"),
    Section("generic"),
    Section("parsing_error"),
    Section("parsing_error_source", highlight="text"),
    Section("cause_header", prefix="### "),
    Section("cause"),
    Section("last_call_header", prefix="### "),
    Section("last_call_source", highlight="text"),
    Section("last_call_variables_header", prefix="#### "),
    Section("last_call_variables", highlight="text"),
    Section("exception_raised_header", prefix="### "),
    Section("exception_raised_source", highlight="text"),
    Section("exception_raised_variables_header", prefix="#### "),
    Section("exception_raised_variables", highlight="text"),
]


def friendly_traceback_markdown(info, level=None, include=None):
    """Traceback formatted with full information but with markdown syntax."""
    result = []

    for item in MARKDOWN_ITEMS:
        if item.name in info:
            line = info[item.name]
            if not isinstance(line, str):
                line = "\n".join(line)
            if item.name == "simulated_python_traceback":
                line = line.replace("Simulated Traceback", "Traceback")
            if item.prefix[:1] == "#":
                line = line.rstrip(": ")  # Do not end titles with column
            if item.highlight:
                line = "    :::" + item.highlight + "\n" + indent(line, "    ")
            result.append(item.prefix + line + item.suffix + "\n\n")
    return "\n".join(result)


friendly_traceback.set_formatter(friendly_traceback_markdown)


def run(file, *args):
    start_hint = ""
    if args:
        args = ["--"] + list(args)
        start_hint = (
            "I started it as:\n\n"
            + code(file + " " + " ".join(shlex.quote(a) for a in args)),
        )
    try:
        proc = subprocess.run(
            [
                "python3",
                "-m",
                "friendly_traceback",
                "--formatter",
                "correction_helper.friendly_traceback_markdown",
                file,
                *args,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )
    except subprocess.CalledProcessError as err:
        stdout = stderr = ""
        if err.stdout:
            if len(err.stdout) > 1_000:
                stdout = f"Your code printed {len(err.stdout)} characters before being interrupted."
            else:
                stdout = "Your code printed:\n\n" + code(err.stdout)
        if err.stderr:
            if len(err.stderr) > 1_000:
                stdout = f"Your code printed {len(err.stderr)} characters on stderr before being interrupted."
            else:
                stdout = "Found this on stderr:\n\n" + code(err.stderr)
        if err.returncode == -9:
            fail(
                "I had to halt your program, sorry...",
                "It were either too slow, or consuming too much resources.",
                "Check for an infinite loop maybe?",
                start_hint,
                stdout,
                stderr,
            )
        fail(
            f"Your program exited with the error code: {err.returncode}.",
            start_hint,
            stdout,
            stderr,
        )
    except MemoryError:
        fail(
            "Your program is eating up all the memory! Check for infinite loops maybe?",
            start_hint,
        )
    if proc.stderr:
        if (
            "EOF when reading a line" in proc.stderr
            and "input" in Path(file).read_text()
        ):
            fail(
                "Don't use the `input` builtin, there's no human to interact with here."
            )
        else:
            fail(proc.stderr)
    return proc.stdout.rstrip()


def code_or_repr(some_string):
    """Display some string for a student.

    If the string is short enough, return it between backticks, else
    return it as a Markdown code block.
    """
    if len(some_string) < 10 and "`" not in some_string:
        return f" `{some_string}`"
    else:
        return "\n\n" + code(some_string)


def compare(my, theirs, preamble=""):
    """Compare two results: mine (expected to be the right one) and theirs
    (the student output).

    Both can be multi-lines, and if they differ, a proper message will
    be raised, using correction_helper.fail.

    """
    if my.strip() == theirs.strip():
        return
    for line, (m, t) in enumerate(
        zip_longest(my.split("\n"), theirs.split("\n")), start=1
    ):
        if m != t:
            if m is None:
                fail(
                    preamble,
                    _("Unexpected line {line}, you gave:").format(line=line)
                    + code_or_repr(t),
                    _("Just in case it helps, here's your full output:"),
                    code(theirs),
                )
            elif t is None:
                fail(
                    preamble,
                    _(
                        "Your output is too short, missing line {line}, I'm expecting:"
                    ).format(line=line)
                    + code_or_repr(m),
                    _("Just in case it helps, here's your full output:"),
                    code(theirs),
                )
            else:
                hint = ""
                trailer = ""
                if t != theirs:
                    trailer = (
                        _("Just in case it helps, here's your full output:")
                        + "\n\n"
                        + code(theirs)
                    )
                if m and t:
                    if t[0] == " " and m[0] != " ":
                        hint = (
                            "\n\n" + "(Notice your line starts with a space, not mine.)"
                        )
                    if t[-1] == " " and m[-1] != " ":
                        hint = (
                            "\n\n" + "(Notice your line ends with a space, not mine.)"
                        )
                fail(
                    preamble,
                    _("On line {line} I'm expecting:").format(line=line)
                    + code_or_repr(m),
                    _("You gave:") + code_or_repr(t),
                    hint,
                    trailer,
                )
    fail(
        preamble,
        "Looks like a wrong answer, expected:",
        code(my),
        "you gave:",
        code(theirs),
    )
