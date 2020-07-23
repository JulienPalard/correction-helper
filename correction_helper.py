from io import StringIO
import sys
from traceback import format_exc
from contextlib import redirect_stdout, redirect_stderr
from textwrap import indent
from contextlib import contextmanager

import friendly_traceback

friendly_traceback.set_formatter(friendly_traceback.formatters.markdown)


def code(text, language="python"):
    return "    :::" + language + "\n" + indent(str(text), "    ")


def stderr(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def fail(text):
    """Print text on stderror and exit with failure (code=1).
    """
    stderr(text)
    sys.exit(1)


def clean_format_exc():
    """Like traceback.format_exc but take care of eliminating
    correction_helper from the traceback, it's not usefull for the
    students.
    """
    limit = -10
    for limit in range(-10, 0):
        exc = format_exc(limit=limit)
        if "correction_helper.py" not in exc:
            return exc
    return format_exc()


def _handle_student_exception(prefix, friendly=False):
    if prefix:
        stderr(prefix, end="\n\n")
    if friendly:
        friendly_traceback.explain()
    else:
        stderr(code(clean_format_exc(), "pytb"))
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
    friendly=False,
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
