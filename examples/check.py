import correction_helper as checker

# First, exclude our code from tracebacks to avoid surprising students:
checker.exclude_file_from_traceback(__file__)

with checker.student_code():
    # Here, if the import fail, if the student prints, or try to exit,
    # it will be reported with a nice message in Markdown, and your process
    # will exit with code 1.
    from solution import fib


def check_solution(n, expected):
    with checker.student_code(print_expect=expected):
        # Here, if the function raises, if the student prints, or try to exit,
        # it will be reported too, and exit with code 1 too.
        # If the student prints what is expected to be returned
        # (the `print_expect` parameter), we told that, too.
        result = fib(n)
    if result != expected:
        checker.fail(
            f"When asked for fib({n}) your code give:",
            checker.code(result, "text"),
            "while I expected:",
            checker.code(expected, "text"),
        )


check_solution(1, 1)
check_solution(2, 1)
check_solution(16, 987)
