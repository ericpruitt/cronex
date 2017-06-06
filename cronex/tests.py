#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import unittest
from ddt import ddt, data, unpack

# Add the parent directory relative to the test case because we assume the
# test will be in a subdirectory relative to the main code base.
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir))

import cronex as cx


class CronexInputExceptionCase(unittest.TestCase):
    """testing varies exceptions"""

    @staticmethod
    def regex_exception_invalid_use(s):
        return '.*Invalid {}.*'.format(s)

    @staticmethod
    def regex_exception_too_few_fields(s):
        return '.*fields but found.*'

    def assertExceptionRaised(self, expression, field, regex_method):
    # expression: cron expression ('* * * * *', etc.)
    # field: field being tested ('hour', 'minute', 'second', etc.)
    # regex_method: converting field into regex matching the exception message
        expected_regex = regex_method(field)
        with self.assertRaisesRegex(cx.Error, expected_regex):
            cx.CronExpression(
                expression,
                with_seconds=('second' in field),
                with_years=('year' in field)
            )

@ddt
class CronexInputException(CronexInputExceptionCase):
    '''testing FieldSyntaxError'''
    @unpack
    @data(# invalid field characters
          ['0  0  1  1  x',       'days of the week'],
          ['0  1  2  x  2',       'month'],
          ['0  1  x  3  2',       'day'],
          ['0  x  2  3  2',       'hour'],
          ['x  0  2  3  2',       'minute'],
          ['x  0  2  3  2  1',    'second'],
          ['0  0  2  3  2  1  x', 'year'],
          # invalid repetition periods
          ['0  0  1  1  %x',      'days of the week'],
          ['0  1  2  %x 2',       'month'],
          ['0  1  %x 3  2',       'day'],
          ['0  %x 2  3  2',       'hour'],
          ['%x 0  2  3  2',       'minute'],
          ['%x 0  2  3  2  1',    'second'],
          ['0  0  2  3  2  1 %x', 'year'],
          ["*  *  *  *  %-1",     'days of the week'],
          ["%1 *  *  *  *",       'minute'],
          ["*  %1 *  *  *",       'hour'],
          ["*  *  %1 *  *",       'day'],
          ["*  *  *  %1 *",       'month'],
          ["*  *  *  *  %1",      'days of the week'],
          ["%0 *  *  *  *",       'minute'],
          ["*  %0 *  *  *",       'hour'],
          ["*  *  %0 *  *",       'day'],
          ["*  *  *  %0 *",       'month'],
          ["*  *  *  *  %0",      'days of the week'],
    )
    def test_FieldSyntaxError(self, exp, field):
        self.assertExceptionRaised(exp, field, self.regex_exception_invalid_use)

    '''testing OutOfBounds'''
    @unpack
    @data(# fields are out of bounds
          ['61 23 27 12 1',       'minute'],
          ['59 25 27 12 1',       'hour'],
          ['59 23 32 12 1',       'day'],
          ['59 23 27 13 1',       'month'],
          ['59 23 27 12 9',       'days of the week'],
          ['61 59 23 27 12 1',    'second'],
          ['59 23 27 12 1  1969', 'year'],
          ['%1 23 27 12 1',       'minute'],
          ['59 %1 27 12 1',       'hour'],
          ['59 23 %1 12 1',       'day'],
          ['59 23 27 %1 1',       'month'],
          ['%1 59 23 27 12 1',    'second'],
          ['59 23 27 12 1 %1',    'year'],
          ["99 *  *  *  *",       'minute'],
          ["*  99 *  *  *",       'hour'],
          ["*  *  99 *  *",       'day'],
          ["*  *  *  99 *",       'month'],
          ["*  *  *  *  99",      'days of the week'],
          ["-1 *  *  *  *",       'minute'],
          ["*  -1 *  *  *",       'hour'],
          ["*  *  0  *  *",       'day'],
          ["*  *  *  0  *",       'month'],
          ["*  *  *  *  -1",      'days of the week'],
    )
    def test_OutOfBounds(self, exp, field):
        self.assertExceptionRaised(exp, field, self.regex_exception_invalid_use)

    '''testing InvalidUsage'''
    @unpack
    @data(# syntactically invalid "L"
          ['L  23 27 12 1',       'minute'],
          ['59 L  27 12 1',       'hour'],
          ['59 23 27 L  1',       'month'],
          ['61 59 23 27 12 L',    'second'],
          ['59 23 27 12 1  L',    'year'],
          ['L-1 23 27 12 1',      'minutes'],
          ['59 L-1 27 12 1',      'hours'],
          ['59 23 27 L-1 1',      'month'],
          ['59 23 27 12 L-1',     'days of the week'],
          ['61 59 23 27 12 L-1',  'second'],
          ['59 23 27 12 1  L-1',  'year'],
          ['59 23 27 12 %2',      'days of the week'],
          ["L * * * *",           'minute'],
          ["* L * * *",           'hour'],
          ["* * 99L * *",         'day'],
          ["* * 0L * *",          'day'],
          ["* * * L *",           'month'],
          ["* * * * L",           'days of the week'],  # failed
          ["* * * * 9L",          'days of the week'],
          ["* * * * -9L",         'days of the week'],
          # syntactically invalid "?"
          ['?  23 27 12 1',       'minute'],
          ['59 ?  27 12 1',       'hour'],
          ['59 23 27 ?  1',       'month'],
          ['?  59 23 27 12 1',    'second'],
          ['59 23 27 12 1  ?',    'year'],
          # syntactically invalid "#"
          ["# * * * *",           'minute'],
          ["* # * * *",           'hour'],
          ["* * # * *",           'day'],
          ["* * * # *",           'month'],
          ["* * * * 9#9L",        'days of the week'],
          # syntactically invalid "W"
          ["5W * * * *",          'minute'],  # failed
          ["* 5W * * *",          'hour'],  # failed
          ["* * 99W * *",         'day'],
          ["* * 0W * *",          'day'],
          ["* * W0 * *",          'day'],
          ["* * * 5W *",          'month'],  # failed
          ["* * * * 5W",          'days of the week'],  #failed
          # not lonely asterisk
          ["*,5 * * * *",         'minute'],
          ["* *,1-9 * * *",       'hour'],
          ["* * *,4 * *",         'day'],
          ["* * * *,11 *",        'month'],
          ["* * * * *,6",         'days of the week'],
    )
    def test_InvalidUsage(self, exp, field):
        self.assertExceptionRaised(exp, field, self.regex_exception_invalid_use)

    '''testing MisingFieldsError'''
    @unpack
    @data(["*",                ''],
          ["* *",              ''],
          ["* * *",            ''],
          ["* * * *",          ''],
          ['0  1  2  3',       ''],
          ['0  1  2  3  4',    'second'],
          ['0  1  2  3  4',    'year'],
          ['0  1  2  3  4  5', 'second year'],
    )
    def test_MisingFieldsError(self, exp, field):
        self.assertExceptionRaised(exp, field, self.regex_exception_too_few_fields)


class CronexEqualityCase(unittest.TestCase):
    """testing two cron expressions to end up as the same cronex object using
    conveniently added __eq__ method"""

    def assertCronExpressionsEqual(self, ex1, ex2, year_second):
        cx1 = cx.CronExpression(ex1,
            with_seconds=('second' in year_second),
            with_years=('year' in year_second)
        )
        cx2 = cx.CronExpression(ex2,
            with_seconds=('second' in year_second),
            with_years=('year' in year_second)
        )
        self.assertTrue(cx1 == cx2)

@ddt
class CronexEquality(CronexEqualityCase):

    '''testing full substitutions'''
    @unpack
    @data(["@yearly",   "0 0 1 1 *", ''],
          ["@annually", "0 0 1 1 *", ''],
          ["@monthly",  "0 0 1 * *", ''],
          ["@weekly",   "0 0 * * 0", ''],
          ["@daily",    "0 0 * * *", ''],
          ["@midnight", "0 0 * * *", ''],
          ["@hourly",   "0 * * * *", ''],
    )
    def test_full_substitutions(self, ex1, ex2, year_second):
        self.assertCronExpressionsEqual(ex1, ex2, year_second)

    '''testing months and dows substitutions'''
    @unpack
    @data(["* * * jan *",
           "* * * 1   *",
           ''],  # failed
          ["* * * jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec *",
           "* * * 1,  2,  3,  4,  5,  6,  7,  8,  9,  10, 11, 12  *",
           ''],  # failed
          ["* * * * sun,mon,tue,wed,thu,fri,sat",
           "* * * * 0,  1,  2,  3,  4,  5,  6",
           ''],  # failed
    )
    def test_months_dows_substitutions(self, ex1, ex2, year_second):
        self.assertCronExpressionsEqual(ex1, ex2, year_second)


class MiscTests(unittest.TestCase):
    def test_unicode_is_accepted_in_python2(self):
        if sys.version_info.major > 2:
            return
        cx.CronExpression(unicode("* * * * * ABC"))


if __name__ == "__main__":
    unittest.main()
