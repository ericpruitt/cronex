#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import contextlib
import sys
import traceback
import unittest


class Error(Exception):
    """
    Module-specific base exception class.
    """


class NonFatalAssertionError(AssertionError):
    """
    Exception raised when an assertion in a method called with `fatal=False`
    fails.
    """


class FatalErrorIndicatorException(Error):
    """
    Exception raised when an assertion in a method called with `fatal=True`
    fails or the method raised an exception with an unrecognized type (by
    default, anything other than "AssertionError").
    """


class TestFailure(Error):
    """
    Exception raised when a test method fails with multiple exceptions with
    differing types.
    """


class MultipleCauseTestFailure(TestFailure):
    """
    Exception raised when a test method fails with multiple exceptions with
    differing types.
    """


class TestCaseWithNonFatalAssertions(unittest.TestCase):
    """
    The class behaves mostly like the standard library's unittest.TestCase, but
    all assertion methods are modified so they accept an extra argument, the
    boolean keyword "fatal" so the user can decide whether or not an assertion
    failure causes the test to fail immediately or only once the test method is
    finished. If "fatal" is False, the return value of an assertion method is a
    boolean indicating whether assertion succeeded. If "fatal" is True, the
    return value of this function is the value returned by the underlying
    assertion method.
    """
    assertion_errors = dict()
    failure_exception = unittest.TestCase.failureException
    non_fatal_assertion_error = NonFatalAssertionError

    def _trace(self, tb=None):
        """
        Return a textual stack trace that removes frames that are irrelevant to
        the user's test suite.

        Returns: The stack trace as a string that may have embedded newlines.
        """
        # TODO: figure out when to use sys.exc_info.
        if tb is None:
            stack = traceback.extract_stack()
            del stack[-2:]
            del stack[:self._ignored_frames_from_head]
        else:
            stack = traceback.extract_tb(tb)

        return "".join(traceback.format_list(stack)).rstrip("\n")

    def __getattribute__(self, name):
        """
        Intercept requests for callable attributes that start with "assert" or
        "test" and return wrapped versions of the methods.
        """
        attribute = object.__getattribute__(self, name)

        if not name.startswith(("assert", "test")) or not callable(attribute):
            return attribute

        # Return a wrapper that implements support for the "fatal" keyword.
        elif name.startswith("assert"):
            def method(*args, **kwargs):
                fatal = kwargs.pop("fatal", False)
                errors = self.assertion_errors[self]

                try:
                    result = attribute(*args, **kwargs)
                    return result if fatal else True
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception as e:
                    exception_type = type(e)
                    if not fatal and isinstance(e, self.failure_exception):
                        exception_type = self.non_fatal_assertion_error

                    errors.append((exception_type, e, self._trace()))
                    if fatal:
                        raise FatalErrorIndicatorException()
                    return False

        # The wrapped version of the test method delays reporting non-fatal
        # errors until there is a fatal assertion failure or the original test
        # method has finished running.
        elif name.startswith("test"):
            def method(*args, **kwargs):
                self._ignored_frames_from_head = len(traceback.extract_stack())
                errors = self.assertion_errors.setdefault(self, list())

                try:
                    result = attribute(*args, **kwargs)
                except (KeyboardInterrupt, SystemExit):
                    raise
                except FatalErrorIndicatorException:
                    pass
                except:
                    error_type, error, tb = sys.exc_info()
                    errors.append((error_type, error, self._trace(tb)))
                finally:
                    del self.assertion_errors[self]

                if not errors:
                    return result

                if len(errors) == 1:
                    error_type, error, stack = errors[0]
                    raise error_type("%s\n%s" % (error, stack))

                lines = ["%d exceptions raised during test;" % (len(errors), )]
                error_types = set([t for t, _, _ in errors])

                for n, (error_type, error, stack) in enumerate(errors, 1):
                    if n > 1:
                        lines.append("--")

                    lines.append("Traceback #%d:" % (n, ))
                    lines.extend(stack.splitlines())
                    lines.append("%s: %s" % (error_type.__name__, error))

                raised_error_type = TestFailure
                if error_types:
                    raised_error_type = MultipleCauseTestFailure

                raise raised_error_type("\n  ".join(lines))

        method.__doc__ = attribute.__doc__
        method.__name__ = attribute.__name__
        return method

    @contextlib.contextmanager
    def non_fatal_exception(self):
        """
        Context manager for deferring exception reporting until a unit test has
        concluded.
        """
        errors = self.assertion_errors[self]

        try:
            yield
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            error_type, error, tb = sys.exc_info()
            errors.append((error_type, error, self._trace(tb)))


def main(*args, **kwargs):
    """
    Thin wrapper for unittest.main so code that uses this module can start the
    test suite without importing the standard library's unittest module.
    """
    unittest.main(*args, **kwargs)


main.__doc__ = unittest.main.__doc__
