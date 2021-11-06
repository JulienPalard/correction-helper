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

`print_allowed` can be set to `None` meaning "neither allowed nor
really denied": the student output will be printed along with the
`print_prefix`, but it's not considered a failure.


### `print_prefix="Your code printed something (it should **not**):"`

Message to display when they printed and `print_allowed` was `False`.


## Good practices

Try first if the student code works, if it works, it works. Only if
the code does *not* work, try to understand why.
