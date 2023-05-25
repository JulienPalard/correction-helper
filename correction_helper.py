"""Set of tools to help writing correction bots in Python for Python."""
import gettext
import os
import random
import resource
import shlex
import signal
import subprocess
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from itertools import zip_longest
from pathlib import Path
from textwrap import indent
from typing import Optional, Sequence, Tuple, Union

import friendly_traceback
from friendly_traceback import exclude_file_from_traceback

__version__ = "2023.5"

friendly_traceback.set_lang(os.environ.get("LANGUAGE", "en"))

exclude_file_from_traceback(__file__)

_ = gettext.translation("check", Path(__file__).parent, fallback=True).gettext


def code(text, language="text"):
    """Transform given text as a Markdown code block."""
    return "    :::" + language + "\n" + indent(str(text), "    ")


def print_stderr(*args, **kwargs):
    """`print` wrapper outputing to stderr."""
    print(*args, **kwargs, file=sys.stderr)


def fail(*args, sep="\n\n"):
    """Print args on stderror and exit with failure (code=1).

    By default, if multiple args are given, they are separated by two
    newlines, usefull to build Markdown paragraphs.
    """
    admonition("failure", sep.join(args))
    sys.exit(1)


def congrats():
    """Generate a generic congratulation sentence."""
    if os.environ.get("LANGUAGE", "") == "fr":
        begin = ["Joli", "Bravo", "Bon boulot", "Bien joué", "Super", "Génial", "Bien"]
        end = [
            "Belle implèmentation",
            "Bonne réponse",
            "C'est juste",
            "C'est bon pour moi",
            "Cette réponse est correcte",
            "C'est correct",
        ]
        sep = " "
    else:
        begin = ["Congrats", "Nice job", "Well done", "Spot on", "Bravo", "Good"]
        end = [
            "Your exercise is OK",
            "Right answer",
            "Looks good to me",
            "Your answer is correct",
            "Correct answer",
        ]
        sep = ""
    return " ".join(
        [
            random.choice(begin) + sep + "!" * random.randint(1, 5),
            random.choice(end) + sep + "!" * random.randint(1, 5),
            random.choice("     🚀🎉🙌🏆🥇🎯💯"),
        ]
    ).strip()


def _handle_student_exception(prefix: Optional[Sequence[str]] = None):
    """Handle a student exception.

    Can preprend an optional prefix.

    Use friendly to display a friendly explanation.
    """
    if prefix:
        print_stderr(*prefix, sep="\n\n", end="\n\n")
    friendly_traceback.explain_traceback()
    sys.exit(1)


class Run:
    """Representation for a program or function run storing stdout and stderr."""

    def __init__(self, stdout: StringIO, stderr: StringIO):
        """Create a Run instance from two StringIO (or Twin instances)."""
        self.stdout = stdout
        self.stderr = stderr

    @property
    def out(self):
        """Stdout, stripped."""
        return self.stdout.getvalue().strip()

    @property
    def err(self):
        """Stderr, stripped."""
        return self.stderr.getvalue().strip()


@contextmanager
def deadline(timeout=1):
    """Context manager raising a TimeoutError after a given deadline in seconds."""

    def handler(signum, frame):
        raise TimeoutError

    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    yield
    signal.alarm(0)


def _prepare_message(
    prefix: Union[Sequence[str], str], message: Union[Sequence[str], str, None] = None
) -> Tuple[str, ...]:
    if isinstance(prefix, str):
        prefix = (prefix,)
    else:
        prefix = tuple(prefix)
    if message is None:
        return prefix
    if isinstance(message, str):
        message = (message,)
    else:
        message = tuple(message)
    return prefix + message


@contextmanager
def student_code(  # pylint: disable=too-many-arguments,too-many-branches
    *,
    prefix=(),
    exception_prefix="",
    print_allowed=True,  # pylint: disable=redefined-outer-name
    print_hook=None,
    print_prefix="Your code printed:",
    too_slow_message="Your program looks too slow, looks like an infinite loop.",
    timeout=1,
):
    """Execute student code under surveillance.

    It help them spot common errors like:
    - using `input()`
    - using `exit()`
    - raising an exception (pretty printing it in Markdown)

    print_allowed can take 3 values:
    - `True`: Prints are allowed (and displayed).
    - `None`: Prints are allowed (but not displayed).
    - `False`: Prints are disallowed (and displayed).

    print_hook, if given, take precedence over print_allowed:
    print_hook is simply called with what the code printed as arguments, like:

        print_hook(run.out, run.err)

    Typical usage:
        print_hook=print_allowed()
        print_hook=print_denied()
        print_hook=print_to_admonition()

    (Check the optional arguments to print_allowed, print_denied, and
    print_to_admonition to personalize the messages.)

    `prefix`, if given, is always prefixed to `print_prefix` and
    `exception_prefix` helping to deduplicate strings.

    Use as:
    with student_code() as run:
        their_value = their_function(your_argument)
    print(run.out, run.err)  # You have access to what they tried to write
                             # to stdout and stderr (both stripped).

    """
    exception_prefix = _prepare_message(prefix, exception_prefix)
    print_prefix = _prepare_message(prefix, print_prefix)
    too_slow_message = _prepare_message(prefix, too_slow_message)

    old_stdin = sys.stdin
    capture = Run(StringIO(), StringIO())
    old_soft, old_hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(  # 1GB should be enough for anybody
        resource.RLIMIT_AS, (1024**3, old_hard)
    )
    try:
        sys.stdin = None
        with redirect_stdout(capture.stdout):
            with redirect_stderr(capture.stderr):
                with deadline(timeout):
                    yield capture
                resource.setrlimit(resource.RLIMIT_AS, (old_soft, old_hard))
    except TimeoutError:
        resource.setrlimit(resource.RLIMIT_AS, (old_soft, old_hard))
        fail(*too_slow_message)
    except SystemExit:
        resource.setrlimit(resource.RLIMIT_AS, (old_soft, old_hard))
        fail(
            """Your program tried to exit,
remove any `exit()` or `sys.exit()` from your code,
else I won't be able to check it."""
        )
    except RuntimeError as err:
        resource.setrlimit(resource.RLIMIT_AS, (old_soft, old_hard))
        if "lost sys.stdin" not in str(err):
            _handle_student_exception(exception_prefix)
        fail("Don't use the `input` builtin, there's no human to interact with here.")
    except:  # noqa  pylint: disable=bare-except
        resource.setrlimit(resource.RLIMIT_AS, (old_soft, old_hard))
        _handle_student_exception(exception_prefix)
    finally:
        resource.setrlimit(resource.RLIMIT_AS, (old_soft, old_hard))
        sys.stdin = old_stdin
    if capture.err or capture.out:
        if print_hook:
            print_hook(capture.out, capture.err)
        elif print_allowed is not None:
            print(*print_prefix, sep="\n\n", end="\n\n")
            if capture.err:
                print(code(capture.err, language="text"))
            if capture.out:
                print(code(capture.out, language="text"))
            if print_allowed is False:
                sys.exit(1)


def print_denied(message="Your code printed:"):
    """To be used as print_hook to deny prints.

    >>> with student_code(print_hook=print_denied("Your function printed:")):
    ...     print(42)
    Your function printed:

        :::text
        42

    (Then exit with an error code of 1 if the student has printed.)
    """
    message = _prepare_message(message)

    def print_cb(out, err):
        if err or out:
            print(*message, sep="\n\n", end="\n\n")
            if err:
                print(code(err))
            if out:
                print(code(out))
            sys.exit(1)

    return print_cb


def print_silent():
    """To be used as print_hook to silence prints.

    >>> with student_code(print_hook=print_allowed("Your function printed:")) as run:
    ...     print(42)
    >>> print(run.out)
    42
    """
    return lambda out, err: ...


def print_allowed(message="Your code printed:"):
    """To be used as print_hook to allow prints.

    >>> with student_code(print_hook=print_allowed("Your function printed:")):
    ...     print(42)
    Your function printed:

        :::text
        42
    """
    message = _prepare_message(message)

    def print_cb(out, err):
        if err or out:
            print(*message, sep="\n\n", end="\n\n")
        if err:
            print(code(err))
        if out:
            print(code(out))

    return print_cb


def print_to_admonition(header="Your code printed:", admonition_type="info"):
    """To be used as print_hook, renders prints as a Markdown admonition.

    >>> with student_code(print_hook=print_to_admonition("info", "FYI it printed:")):
    ...     print(42)
    !!! info ""

        FYI it printed:

            :::text
            42
    """
    if not isinstance(header, str):
        header = "\n\n".join(header)
    return lambda out, err: admonition(
        admonition_type,
        header,
        code(out + "\n" + err),
    )


def admonition(admonition_type, *body, title=""):
    """Build a Markdown Admonition.

    >>> admonition("note", "Hello world.")
    !!! note ""
        Hello world.
    """
    print(f'!!! {admonition_type} "{title}"\n')
    for item in body:
        print(indent(item, "    "), sep="\n\n", end="\n\n")


@dataclass
class Section:
    """A section of friendly output."""

    name: str
    prefix: str = ""
    suffix: str = ""
    highlight: Union[str, bool] = False


MARKDOWN_ITEMS = [
    Section("header", prefix="## "),
    Section("shortened_traceback", highlight="pytb"),
    Section("suggest"),
    Section("generic"),
    Section("parsing_error"),
    Section("parsing_error_source", highlight="text"),
    Section("cause_header", prefix="### "),
    Section("cause"),
    Section("last_call_header", prefix="### "),
    Section("last_call_source", highlight="text"),
    Section("last_call_variables", highlight=True),
    Section("exception_raised_header", prefix="### "),
    Section("exception_raised_source", highlight="text"),
    Section("exception_raised_variables", highlight=True),
]


def friendly_traceback_markdown(
    info: friendly_traceback.typing_info.Info,
    include: friendly_traceback.typing_info.InclusionChoice = None,  # pylint: disable=unused-argument
) -> str:
    """Traceback formatted with full information but with markdown syntax."""
    result = []
    for item in MARKDOWN_ITEMS:
        if item.name in info:
            line = info[item.name]  # type: ignore
            if not isinstance(line, str):
                line = "\n".join(line)
            if item.name == "simulated_python_traceback":
                line = line.replace("Simulated Traceback", "Traceback")
            if item.prefix[:1] == "#":
                line = line.rstrip(": ")  # Do not end titles with column
            if item.highlight is True:
                line = indent(line, "    ")
            elif item.highlight:
                line = "    :::" + str(item.highlight) + "\n" + indent(line, "    ")
            result.append(item.prefix + line + item.suffix + "\n\n")
    return "\n".join(result)


friendly_traceback.set_formatter(friendly_traceback_markdown)


def truncate(string):
    """May truncate string if it's too long."""
    if os.environ.get("CORRECTION_HELPER_NO_TRUNCATE"):
        return string
    if len(string) < 4096:
        return string
    return string[:512] + f"\n…({len(string)-1024} truncated chars)…\n" + string[-512:]


def run(file, *args):  # pylint: disable=too-many-branches
    """subprocess.run wrapper specialized to run Python with friendly."""
    start_hint = ""
    if args:
        start_hint = "I started it as:\n\n" + code(
            file + " " + " ".join(shlex.quote(a) for a in args)
        )
        args = ["--"] + list(args)
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
            stdin=subprocess.DEVNULL,
            universal_newlines=True,
            check=True,
        )
    except subprocess.CalledProcessError as err:
        stdout = stderr = ""
        if err.stdout:
            stdout = "Your code printed:\n\n" + code(truncate(err.stdout))
        if err.stderr:
            stderr = "Found this on stderr:\n\n" + code(truncate(err.stderr))
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
        if "EOF when reading a line" in proc.stderr and "input" in Path(file).read_text(
            encoding="UTF-8"
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
    return "\n\n" + code(some_string)


def compare(expected, theirs, preamble=""):
    """Compare two results.

    expected (the right one) and theirs (student output).

    Both can be multi-lines, and if they differ, a proper message will
    be raised, using correction_helper.fail.
    """
    if expected.strip() == theirs.strip():
        return
    for line, (expected_line, their_line) in enumerate(
        zip_longest(expected.split("\n"), theirs.split("\n")), start=1
    ):
        if expected_line != their_line:
            if expected_line is None:
                fail(
                    preamble,
                    _("Unexpected line {line}, you gave:").format(line=line)
                    + code_or_repr(their_line),
                    _("Just in case it helps, here's your full output:"),
                    code(theirs),
                )
            elif their_line is None:
                fail(
                    preamble,
                    _(
                        "Your output is too short, missing line {line}, I'm expecting:"
                    ).format(line=line)
                    + code_or_repr(expected_line),
                    _("Just in case it helps, here's your full output:"),
                    code(theirs),
                )
            else:
                hint = ""
                trailer = ""
                if their_line != theirs:
                    trailer = (
                        _("Just in case it helps, here's your full output:")
                        + "\n\n"
                        + code(theirs)
                    )
                if expected_line and their_line:
                    if their_line[0] == " " and expected_line[0] != " ":
                        hint = (
                            "\n\n" + "(Notice your line starts with a space, not mine.)"
                        )
                    if their_line[-1] == " " and expected_line[-1] != " ":
                        hint = (
                            "\n\n" + "(Notice your line ends with a space, not mine.)"
                        )
                fail(
                    preamble,
                    _("On line {line} I'm expecting:").format(line=line)
                    + code_or_repr(expected_line),
                    (_("You gave:") + code_or_repr(their_line))
                    if their_line
                    else _("You gave nothing."),
                    hint,
                    trailer,
                )
    fail(
        preamble,
        "Looks like a wrong answer, expected:",
        code(expected),
        "you gave:",
        code(theirs),
    )
