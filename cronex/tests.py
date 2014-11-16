#!/usr/bin/env python
# -*- coding: utf-8 -*-

import calendar
import datetime
import os
import site
import sys
import time
import unittest

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR

# Python 3 compatibility
if isinstance(map, type):
    xrange = range

# Add the parent directory relative to the test case because we assume the
# test will be in a subdirectory relative to the main code base.
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir))

import cronex


class test_testedmodule(unittest.TestCase):
    def test_substitution(self):
        """
        Verify that the special substitutions are replaced by the correct,
        expanded cron expressions.
        """
        testcases = [("@yearly", "0 0 1 1 *"),
            ("@annually", "0 0 1 1 *"),
            ("@monthly", "0 0 1 * *"),
            ("@weekly", "0 0 * * 0"),
            ("@daily", "0 0 * * *"),
            ("@midnight", "0 0 * * *"),
            ("@hourly", "0 * * * *")]
        for a, b in testcases:
            obj = cronex.CronExpression(a)
            self.assertTrue(b in repr(obj))

    def test_compute_numtab(self):
        """
        Verify that calling compute_numtab after modifying the string-version
        of an expression results in the static trigger-value cache being
        updated.
        """
        testex1 = cronex.CronExpression("*/7 5-10 5 * *")
        testex2 = cronex.CronExpression("*/5 23-2 5 8 *")
        self.assertNotEqual(testex1.string_tab, testex2.string_tab)
        self.assertNotEqual(testex1.numerical_tab, testex2.numerical_tab)
        testex1.string_tab = testex2.string_tab
        testex1.compute_numtab()
        self.assertEqual(testex1.string_tab, testex2.string_tab)
        self.assertEqual(testex1.numerical_tab, testex2.numerical_tab)

    def test_periodics_dom(self):
        """
        Verify that arbitrary-period repeaters in the day-of-the-month field
        work as expected.
        """
        now = int(time.time())
        then = time.gmtime(now - 491 * DAY)
        now_tuple = time.gmtime(now)
        testex = cronex.CronExpression("* * %491 * *")
        self.assertFalse(testex.check_trigger(now_tuple[:5]))
        testex.epoch = tuple(list(then[:5]) + [0])
        self.assertTrue(testex.check_trigger(now_tuple[:5]))
        self.assertTrue(testex.check_trigger(then[:5]))

    def test_periodics_hours(self):
        """
        Verify that arbitrary-period repeaters in the hours field work as
        expected.
        """
        now = int(time.time())
        then = time.gmtime(now - 9001 * HOUR)
        now_tuple = time.gmtime(now)
        testex = cronex.CronExpression("* %9001 * * *")
        self.assertFalse(testex.check_trigger(now_tuple[:5]))
        testex.epoch = tuple(list(then[:5]) + [0])
        self.assertTrue(testex.check_trigger(now_tuple[:5]))
        self.assertTrue(testex.check_trigger(then[:5]))

    def test_periodics_minutes(self):
        """
        Verify that arbitrary-period repeaters in the minutes field work as
        expected.
        """
        now = int(time.time())
        then = time.gmtime(now - 814075 * MINUTE)
        now_tuple = time.gmtime(now)
        testex = cronex.CronExpression("%814075 * * * *")
        self.assertFalse(testex.check_trigger(now_tuple[:5]))
        testex.epoch = tuple(list(then[:5]) + [0])
        self.assertTrue(testex.check_trigger(now_tuple[:5]))
        self.assertTrue(testex.check_trigger(then[:5]))

    def test_periodics_month(self):
        """
        Verify that arbitrary-period repeaters in the month field work as
        expected.
        """
        now = int(time.time())
        then = time.gmtime(now - 1337 * DAY)
        now_tuple = time.gmtime(now)
        curmon = now_tuple[1]
        thnmon = then[1]
        if curmon < thnmon:
            curmon += 12
        per = 36 + curmon - thnmon
        testex = cronex.CronExpression("* * * %%%i *" % per)
        self.assertFalse(testex.check_trigger(now_tuple[:5]))
        testex.epoch = tuple(list(then[:5]) + [0])
        self.assertTrue(testex.check_trigger(now_tuple[:5]))
        self.assertTrue(testex.check_trigger(then[:5]))

    def test_parse_atom(self):
        """
        Verify that parsing atoms returns sets containing all of the expected
        values.
        """
        input_expect = [
            (('5-10', (1, 20)), set([5, 6, 7, 8, 9, 10])),
            (('10-5', (1, 12)), set([10, 11, 12, 1, 2, 3, 4, 5])),
            (('5-10/2', (1, 20)), set([5, 7, 9])),
            (('10-5/2', (1, 12)), set([10, 12, 2, 4])),
            (('11-5/2', (1, 12)), set([11, 1, 3, 5])),
            (('10-5/3', (1, 11)), set([10, 2, 5])),
            (('11-5/3', (1, 14)), set([11, 14, 3])),
            (('*', (1, 100)), set(xrange(1, 101))),
            (('*/5', (1, 100)), set(xrange(1, 101, 5))),
            (('666', (1, 1000)), set([666])),
            (('21-1', (0, 23)), set([21, 22, 23, 0, 1]))]

        for give_the_function, want_from_function in input_expect:
            self.assertEqual(want_from_function,
                cronex.parse_atom(*give_the_function))

    def test_str_and_repr(self):
        """
        Verify that the __repr__ and __str__ return values can be passed to
        eval to generate an identical CronExpression.
        """
        CronExpression = cronex.CronExpression
        testex1 = cronex.CronExpression("*/15 4 1-7 * * TEST___TEST")
        testex2 = eval(repr(testex1))
        self.assertEqual(testex1.string_tab, testex2.string_tab)
        self.assertEqual(testex1.numerical_tab, testex2.numerical_tab)
        self.assertEqual(testex1.comment, testex2.comment)
        self.assertEqual(repr(testex1), str(testex1))

    def test_dom_substitution(self):
        """
        Verify that shortened month names are correctly translated numeric
        indexes.
        """
        testex1 = cronex.CronExpression(
            "* * * jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec *")
        testex2 = cronex.CronExpression("* * * 1,2,3,4,5,6,7,8,9,10,11,12 *")
        self.assertEqual(repr(testex1), repr(testex2))

    def test_dow_substitution(self):
        """
        Verify that shortened days-of-the-week are correctly translated numeric
        indexes.
        """
        testex1 = cronex.CronExpression("* * * * sun,mon,tue,wed,thu,fri,sat")
        testex2 = cronex.CronExpression("* * * * 0,1,2,3,4,5,6")
        self.assertEqual(repr(testex1), repr(testex2))

    def test_dom_either_or_dow(self):
        """
        Verify that combining day of-the-month field and day-of-the-week field
        triggers on either condition matching the current day and that using a
        wild-card day of the month with a day of the week entry doesn't trigger
        every single day.
        """
        # Trigger should fire every Monday or on the 5th day of the month.
        testex = cronex.CronExpression("0 0 5 * mon")
        for e in xrange(1, 30):
            if e in (1, 5, 8, 15, 22, 29):
                self.assertTrue(testex.check_trigger((2010, 11, e, 0, 0)))
            else:
                self.assertFalse(testex.check_trigger((2010, 11, e, 0, 0)))

        # Trigger should fire every Wednesday at midnight.
        testex = cronex.CronExpression("0 0 * * wed")
        for d in xrange(1, 32):
            # In July of 2014, every Wednesday just happens to be on a day of
            # the month that's a multiple of 7.
            if not(d % 7):
                self.assertTrue(testex.check_trigger((2010, 7, d, 0, 0)))
            else:
                self.assertFalse(testex.check_trigger((2010, 7, d, 0, 0)))

    def test_L_in_dow(self):
        """
        Verify that having L in the day-of-the-week field with a number always
        triggers on last occurrence of the corresponding day of the week in any
        given month.
        """
        testex = cronex.CronExpression("0 0 * * 6L")
        # The numbers are the dates of the last Saturday in each month of the
        # year 2010.
        tv = [30, 27, 27, 24, 29, 26, 31, 28, 25, 30, 27, 25]
        for v in xrange(0, 12):
            self.assertTrue((testex.check_trigger((2010, v+1, tv[v], 0, 0))))

    def test_L_in_dom(self):
        """
        Verify that having L in the day-of-the-month field always triggers on
        the last day of the month.
        """
        testex = cronex.CronExpression("0 0 L * *")
        for y in xrange(2000, 2009):
            for v in xrange(1, 13):
                # Checks every day from January 1st 2000 through December 31st
                # 2008 an verifies that the trigger only activates on the last
                # day of the month. The year range was chosen to ensure at leas
                # one leap year would be included in the test.
                lastdom = calendar.monthrange(y, v)[-1]
                for d in xrange(1, lastdom + 1):
                    if d < lastdom:
                        self.assertFalse(testex.check_trigger((y, v, d, 0, 0)))
                    else:
                        self.assertTrue(testex.check_trigger((y, v, d, 0, 0)))

    def test_calendar_change_vs_hour_change(self):
        """
        Verify that a periodic trigger for the day of the month is based on
        calendar days, not 24-hour days.
        """
        # epoch and local differ by < 48 hours but it should be reported based
        # on calendar days, not 24 hour days
        epoch = (2010, 11, 16, 23, 59)
        local_time = (2010, 11, 18, 0, 0)
        testex = cronex.CronExpression("0 0 %2 * *", epoch, -6)
        self.assertTrue(testex.check_trigger(local_time, -6))

    def test_asterisk_is_loney(self):
        """
        Verify that asterisk cannot be combined with other atoms.
        """
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "* *,1-9 * * *")

    def test_dow_occurence(self):
        """
        Verify that using "#" to find the Nth occurrence of a given day of the
        week works correctly.
        """
        for dow in xrange(0, 7):
            for occurence in (1, 6):
                day = (7 * (occurence - 1)) + dow + 1
                expression = "0 0 * * %i#%i" % (dow, occurence)
                if occurence > 5:
                    # There can never be more than 5 occurrences of a given day
                    # of the week in one month.
                    self.failUnlessRaises(ValueError, cronex.CronExpression,
                        expression)
                elif day < 32:
                    testex = cronex.CronExpression(expression)
                    self.assertTrue(testex.check_trigger(
                        (2011, 5, day, 0, 0)))
                    if day > 8:
                        self.assertFalse(testex.check_trigger(
                            (2011, 5, max(day - 7, 1), 0, 0)))
                    elif day < 25:
                        self.assertFalse(testex.check_trigger(
                            (2011, 5, max(day + 7, 1), 0, 0)))

    def test_nearest_weekday(self):
        """
        Verify that using "W" to find the nearest weekday works correctly.
        """
        month = 4
        year = 1991
        lastdom = calendar.monthrange(year, month)[-1]

        for day in xrange(1, 31):
            dow = (datetime.date.weekday(
                datetime.date(year, month, day)) + 1) % 7
            testex = cronex.CronExpression("0 0 %iW * *" % day)
            if dow == 0 or dow == 6:
                self.assertFalse(testex.check_trigger(
                    (year, month, day, 0, 0)))
                at_least_one_of_them = (
                    testex.check_trigger((year, month, max(day - 1, 1), 0, 0))
                    or
                    testex.check_trigger((year, month, max(day - 2, 1), 0, 0))
                    or
                    testex.check_trigger(
                        (year, month, min(day + 1, lastdom), 0, 0))
                    or
                    testex.check_trigger(
                        (year, month, min(day + 2, lastdom), 0, 0)))
                self.assertTrue(at_least_one_of_them)
            else:
                self.assertTrue(
                    testex.check_trigger((year, month, day, 0, 0)))

    def test_strict_range_bounds(self):
        """
        Verify that having numbers outside of the reasonable ranges for each
        field raises an exception. Tests both upper and lower bounds.
        """
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "1000 * * * *")
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "* 1000 * * *")
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "* * 1000 * *")
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "* * * 1000 *")
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "* * * * 1000")
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "-1 * * * *")
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "* -1 * * *")
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "* * 0 * *")
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "* * * 0 *")
        self.failUnlessRaises(ValueError,
            cronex.CronExpression, "* * * * -1")

    def test_catches_bad_modulus(self):
        """
        Verify that having a trigger with an invalid repetition period raises
        an exception.
        """
        badstuff = [
            "* * * * %-1",
            "%1 * * * *",
            "* %1 * * *",
            "* * %1 * *",
            "* * * %1 *",
            "* * * * %1",
            "%0 * * * *",
            "* %0 * * *",
            "* * %0 * *",
            "* * * %0 *",
            "* * * * %0"
        ]
        for case in badstuff:
            self.failUnlessRaises(ValueError,
                cronex.CronExpression, case)

    def test_catches_bad_W(self):
        """
        Verify that having a syntactically invalid "W" raises an exception.
        """
        badstuff = [
            "5W * * * *",
            "* 5W * * *",
            "* * 99W * *",
            "* * 0W * *",
            "* * W0 * *",
            "* * * 5W *",
            "* * * * 5W",
        ]
        for case in badstuff:
            self.failUnlessRaises(ValueError,
                cronex.CronExpression, case)

    def test_catches_bad_L(self):
        """
        Verify that having a syntactically invalid "L" raises an exception.
        """
        badstuff = [
            "L * * * *",
            "* L * * *",
            "* * 99L * *",
            "* * 0L * *",
            "* * * L *",
            "* * * * L",
            "* * * * 9L",
            "* * * * -9L"]
        for case in badstuff:
            self.failUnlessRaises(ValueError,
                cronex.CronExpression, case)

    def test_catches_bad_Pound(self):
        """
        Verify that having a syntactically invalid "#" raises an exception.
        """
        badstuff = [
            "# * * * *",
            "* # * * *",
            "* * # * *",
            "* * * # *",
            "* * * * 9#9L"]
        for case in badstuff:
            self.failUnlessRaises(ValueError,
                cronex.CronExpression, case)

    def test_fail_on_not_enough_fields(self):
        """
        Verify that an exception is thrown when the cron expression has too few
        fields.
        """
        badstuff = ["*", "* *", "* * *", "* * * *"]
        for case in badstuff:
            self.failUnlessRaises(ValueError, cronex.CronExpression, case)


if __name__ == "__main__":
    unittest.main()
