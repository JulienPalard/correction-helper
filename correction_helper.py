from io import StringIO
import sys
from traceback import format_exception
from contextlib import redirect_stdout, redirect_stderr
from textwrap import indent
from contextlib import contextmanager
import subprocess
import friendly_traceback
from friendly_traceback import exclude_file_from_traceback


exclude_file_from_traceback(__file__)


def code(text, language="text"):
    return "    :::" + language + "\n" + indent(str(text), "    ")


def stderr(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def fail(text):
    """Print text on stderror and exit with failure (code=1).
    """
    stderr(text)
    sys.exit(1)


def _handle_student_exception(prefix, friendly=False):
    etype, value, tb = sys.exc_info()

    if friendly:
        friendly_traceback.core.exception_hook(etype, value, tb)
    else:
        if prefix:
            stderr(prefix, end="\n\n")
        stderr(code("".join(format_exception(etype, value, tb)), "pytb"))
    sys.exit(1)


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


@contextmanager
def student_code(
    exception_prefix="Got an exception:",
    friendly=True,
    print_allowed=False,
    print_prefix="Your code printed something (it should **not**):",
    print_expect=None,
    print_expect_message="""Your code printed what I expected it to return,
so maybe just replace your `print` call by a `return` statement.""",
):
    """Decorator usefull to run student code.

    It help them spot common errors like:
    - using `input()`
    - using `exit()`
    - raising an exception (pretty printing it in Markdown)

    Use as:
    with student_code() as run:
        their_value = their_function(your_argument)
    print(run.out, run.err)  # You have access to what they tried to write
                             # to stdout and stderr (both stripped).
    """
    old_stdin = sys.stdin
    run = Run(StringIO(), StringIO())
    try:
        sys.stdin = None
        with redirect_stdout(run.stdout):
            with redirect_stderr(run.stderr):
                yield run
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
    if not print_allowed:
        if run.err or run.out:
            stderr(print_prefix, end="\n\n")
            if run.err:
                stderr(code(run.err, language="text"))
            if run.out:
                stderr(code(run.out, language="text"))
            if print_expect and run.out == print_expect:
                stderr(print_expect_message, end="\n\n")
            sys.exit(1)


def friendly_traceback_markdown(info, level):
    """Traceback formatted with full information but with markdown syntax."""
    result = []
    friendly_items = [
        ("header", "## ", "\n", ""),
        ("simulated_python_traceback", "", "\n", "pytb"),
        ("generic", "", "\n", ""),
        ("parsing_error", "\n", "\n", ""),
        ("parsing_error_source", "", "", "text"),
        ("cause_header", "### ", "\n", ""),
        ("cause", "", "\n", ""),
        ("last_call_header", "### ", "", ""),
        ("last_call_source", "", "", "text"),
        ("last_call_variables", "\n#### Variables\n\n", "", "text"),
        ("exception_raised_header", "\n### ", "\n", ""),
        ("exception_raised_source", "", "", "text"),
        ("exception_raised_variables", "\n#### Variables:\n\n", "", "text"),
    ]

    for item, prefix, suffix, pygment in friendly_items:
        if item in info:
            line = info[item]
            if not isinstance(line, str):
                line = "\n".join(line)
            if item == "simulated_python_traceback":
                line = line.replace("Simulated Traceback", "Traceback")
            if prefix[:1] == "#":
                line = line.rstrip(": ")  # Do not end titles with column
            if pygment:
                line = "    :::" + pygment + "\n" + indent(line, "    ")
            result.append(prefix + line + suffix)
    return "\n".join(result)


friendly_traceback.set_formatter(friendly_traceback_markdown)


def run(file, *args):
    if args:
        proc = subprocess.run(
            ["python3", file, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
    else:
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
        )
    if proc.stderr:
        fail(proc.stderr)
    return proc.stdout.strip()
