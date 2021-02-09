# Correction Helper

## Project

This is just a set of tools to help writing correction bots in Python for Python.

It is used for [hackinscience](https://hackinscience.org), but could
be used elsewhere.


## Security considerations

Running student code is probably really unsafe, unless you trust your
students not to drop you a backdoor.

This projet does *not* help with security in any ways, maybe take a
look at [firejail](https://github.com/netblue30/firejail) if you have
trust issues (Yes you can use `correction-helper` inside `firejail`).


## Usage

To install it, run: `pip install correction-helper`.


In your checking code, you can use it like this:


### The `student_code` decorator

This decorator is aimed to catch most problems that could happen in
student code, use it simply as:

```python
with student_code():
    their_function()
```

Here is a more complete example:

```python
from correction_helper import fail, student_code

with student_code():
    # Here, if the import fail, if the student prints, or try to exit,
    # it will be reported with a nice message in Markdown, and your process
    # will exit with code 1.
    from solution import missing_card


def check_deck(deck, expected):
    with student_code(print_expect=expected):
        # Here, if the function raises, if the student prints, or try to exit,
        # it will be reported too, and exit with code 1 too.
        # If the student prints what is expected to be returned
        # (the `print_expect` parameter), we told that, too.
        missing = missing_card(deck)
    if missing != expected:
        fail(f"""With the following deck (missing card is `{expected}`):

{code(deck, "text")}

You're returning:

{code(missing, "text")}
""")
```


## Allowed parameters for `student_code`, and their default values

### `exception_prefix="Got an exception:"`

Printed right before the exception, if any.


### `friendly=False`

To use, or not
[friendly-traceback](https://github.com/aroberge/friendly-traceback/)
instead of bare Python exceptions.


### `print_allowed=False`

To allow the use to print to stdout / stderr, you can read what they
printed using the value of the context manager:

```python
with student_code(print_allowed=True) as run:
    their_function()
assert run.stderr == ""
assert run.stdout == "42"
```

### `print_prefix="Your code printed something (it should **not**):"`

Message to display when they printed and `print_allowed` was `False`.


### `print_expect=None`

String that you bet they'll print instead of return.


### `print_expect_message`

Default value:

> Your code printed what I expected it to return
> so maybe just replace your `print` call by a `return` statement.

This is the message displayed when you won you bet with
`print_expect`, they printed instead of returning.


## Good practices

Try first if the student code works, if it works, it works. Only if
the code does *not* work, try to understand why.
