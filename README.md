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

Find a more complete example in the `examples/` directory.


## Allowed parameters for `student_code`, and their default values

### `exception_prefix="I got an exception:"`

Printed right before the exception, if any.

It's allowed to give a list of strings, in which case they'll be
separated by `"\n\n"`, useful to render markdown paragraphs.


### `print_prefix="Your code printed:"`

Message to display before the student prints (in case `print_allowed`
is `False` or `None`).

It's allowed to give a list of strings, in which case they'll be
separated by `"\n\n"`, useful to render markdown paragraphs.


### `too_slow_message="Your program looks too slow, looks like an infinite loop."`

Message to display in case the code runs slower than the given `timeout` (defaults to 1s).

It's allowed to give a list of strings, in which case they'll be
separated by `"\n\n"`, useful to render markdown paragraphs.


### `prefix=()`

A prefix for `print_prefix`, `exception_prefix`, and
`too_slow_message=`, usefull to deduplicate strings, like:

```python
with student_code(
    prefix="While calling blahblah('bar')",
    print_prefix="it printed:",
    exception_prefix="it raised:",
    too_slow_message="it took more than 1s, had to kill it.",
):
    blahblah('bar')
```


### `friendly=False`

To use, or not
[friendly-traceback](https://github.com/aroberge/friendly-traceback/)
instead of bare Python exceptions.


### `print_allowed=True`

To allow or deny the student to print to stdout and stderr.

- `True`: Prints are allowed (and displayed).
- `None`: Prints are allowed (but not displayed).
- `False`: Prints are disallowed (and displayed).

In all cases you can read what they printed using the value of the
context manager:

```python
with student_code(print_allowed=None) as run:
    their_function()
assert run.err == ""
assert run.out == "42"
```


## Good practices

Write the student checking code a you would write unit test for your
own code.
