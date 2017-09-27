#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import time
import sys
import contextlib
import calendar
import itertools

import cronex
import cronex.unittestmixins

"""
CronExpression:
    def __str__(self):
    def __repr__(self):
    def definitely_equivalent(self, other):
    def text(self) (Get / Set)
    def check_trigger(self, when=None):
    def _configure(self, when=None):

# --
def parse_atom(fields, epoch=None):
"""

NUMBER_TO_DOTW = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
}

ANNOTATION_DESCRIPTIONS = {
    cronex.ANNOTATION_DOTW: "A %(value_dotw)s",
    cronex.ANNOTATION_LW: "Last weekday of the month",
    cronex.ANNOTATION_L_LX: "%(value)dD before the end of the month",
    cronex.ANNOTATION_XHX: "%(value_dotw)s number %(count)d",
    cronex.ANNOTATION_XL: "Last %(value_dotw)s of the month",
    cronex.ANNOTATION_XW: "Weekday closest to day %(value)d of the month",
}


class TestCase(cronex.unittestmixins.TestCase.defaults(fatal=False)):
    """
    """


class TestExceptionlessFunctions(TestCase):
    def test_check_monotonic(self):
        test_cases = [
            (False, (1,  (2, 3, 5))),
            (True,  (2,  (2, 3, 5))),
            (True,  (3,  (2, 3, 5))),
            (True,  (4,  (2, 3, 5))),
            (True,  (5,  (2, 3, 5))),
            (True,  (6,  (2, 3, 5))),
            (False, (7,  (2, 3, 5))),
            (True,  (8,  (2, 3, 5))),
            (True,  (9,  (2, 3, 5))),
            (True,  (10, (2, 3, 5))),
            (False, (11, (2, 3, 5))),
            (False, (13, (2, 3, 5))),
            (False, (17, (2, 3, 5))),
            (False, (19, (2, 3, 5))),

            (True,  (117,  (1, ))),
            (False, (117,  (2, ))),
            (True,  (117,  (3, ))),
            (False, (117,  (5, ))),

            # 1291 is prime, so it should only matches series with 1.
            (False, (1291, (2, 3, 5))),
            (True,  (1291, (1, 2, 3, 5))),
        ]

        for expected, args in test_cases:
            self.assertReturns(expected, cronex.check_monotonic, *args)

    def test_simplify_monotonic_series(self):
        test_cases = [
            ((1, ),             range(1, 10)),
            ((2, 3, 5, 7),      range(2, 10)),
            ((3, 4, 5, 7),      range(3, 10)),
            ((4, 5, 6, 7, 9),   range(4, 10)),
            ((5, 6, 7, 8, 9),   range(5, 10)),
            ((6, 7, 8, 9),      range(6, 10)),
            ((7, 8, 9),         range(7, 10)),
            ((8, 9),            range(8, 10)),
            ((9, ),             range(9, 10)),
        ]

        for expected, series in test_cases:
            expected = set(expected)
            got = cronex.simplify_monotonic_series(series)
            self.assertEqual(expected, got)

    def test_annotate(self):
        DOTW = cronex.ANNOTATION_DOTW
        LW = cronex.ANNOTATION_LW
        L_LX = cronex.ANNOTATION_L_LX
        XHX = cronex.ANNOTATION_XHX
        XL = cronex.ANNOTATION_XL
        XW = cronex.ANNOTATION_XW

        year = 2016
        month = 2

        # Most of these annotations were generated using this Bash script:
        #
        #   #!/usr/bin/env bash
        #   for dotw in {0..6}; do
        #       counters[$dotw]=0
        #   done
        #   for day in {1..29}; do
        #       echo -n "$day: ("
        #       dotw="$((day % 7))"
        #       let ++counters[$dotw]
        #       if [[ "$dotw" -ne 0 ]] && [[ "$dotw" -ne 6 ]]; then
        #           echo -n "(XW, $day), "
        #           neighbor=""
        #           case "$day" in
        #             5|12|19|26) neighbor=$((day + 1)) ;;
        #             8|15|22|29) neighbor=$((day - 1)) ;;
        #           esac
        #           test -z "$neighbor" || echo -n "(XW, $neighbor), "
        #       fi
        #       test "$day" -lt 23 || echo -n "(XL, $dotw), "
        #       echo -n "(L_LX, $((29 - day))), "
        #       echo -n "(XHX, $dotw, ${counters[$dotw]}), "
        #       echo -n "(DOTW, $dotw)"
        #       echo "),"
        #   done

        expected_annotations = {
            1: ((XW, 1), (L_LX, 28), (XHX, 1, 1), (DOTW, 1)),
            2: ((XW, 2), (L_LX, 27), (XHX, 2, 1), (DOTW, 2)),
            3: ((XW, 3), (L_LX, 26), (XHX, 3, 1), (DOTW, 3)),
            4: ((XW, 4), (L_LX, 25), (XHX, 4, 1), (DOTW, 4)),
            5: ((XW, 5), (XW, 6), (L_LX, 24), (XHX, 5, 1), (DOTW, 5)),
            6: ((L_LX, 23), (XHX, 6, 1), (DOTW, 6)),
            7: ((L_LX, 22), (XHX, 0, 1), (DOTW, 0)),
            8: ((XW, 8), (XW, 7), (L_LX, 21), (XHX, 1, 2), (DOTW, 1)),
            9: ((XW, 9), (L_LX, 20), (XHX, 2, 2), (DOTW, 2)),
            10: ((XW, 10), (L_LX, 19), (XHX, 3, 2), (DOTW, 3)),
            11: ((XW, 11), (L_LX, 18), (XHX, 4, 2), (DOTW, 4)),
            12: ((XW, 12), (XW, 13), (L_LX, 17), (XHX, 5, 2), (DOTW, 5)),
            13: ((L_LX, 16), (XHX, 6, 2), (DOTW, 6)),
            14: ((L_LX, 15), (XHX, 0, 2), (DOTW, 0)),
            15: ((XW, 15), (XW, 14), (L_LX, 14), (XHX, 1, 3), (DOTW, 1)),
            16: ((XW, 16), (L_LX, 13), (XHX, 2, 3), (DOTW, 2)),
            17: ((XW, 17), (L_LX, 12), (XHX, 3, 3), (DOTW, 3)),
            18: ((XW, 18), (L_LX, 11), (XHX, 4, 3), (DOTW, 4)),
            19: ((XW, 19), (XW, 20), (L_LX, 10), (XHX, 5, 3), (DOTW, 5)),
            20: ((L_LX, 9), (XHX, 6, 3), (DOTW, 6)),
            21: ((L_LX, 8), (XHX, 0, 3), (DOTW, 0)),
            22: ((XW, 22), (XW, 21), (L_LX, 7), (XHX, 1, 4), (DOTW, 1)),
            23: ((XW, 23), (XL, 2), (L_LX, 6), (XHX, 2, 4), (DOTW, 2)),
            24: ((XW, 24), (XL, 3), (L_LX, 5), (XHX, 3, 4), (DOTW, 3)),
            25: ((XW, 25), (XL, 4), (L_LX, 4), (XHX, 4, 4), (DOTW, 4)),
            26: ((XW, 26), (XW, 27), (XL, 5), (L_LX, 3), (XHX, 5, 4),
                 (DOTW, 5)),
            27: ((XL, 6), (L_LX, 2), (XHX, 6, 4), (DOTW, 6)),
            28: ((XL, 0), (L_LX, 1), (XHX, 0, 4), (DOTW, 0)),
            29: ((XW, 29), (XW, 28), (XL, 1), (L_LX, 0), (XHX, 1, 5),
                 (DOTW, 1), (LW, )),
        }

        for day, expected in expected_annotations.items():
            got = cronex.annotate(2016, 2, day)
            iso_date = "%d-%02d-%02d" % (year, month, day)
            self.assertEqual(set(expected), got, iso_date)

        # The last weekday of January 2016 is the 29th, so it is annotated as
        # the nearest weekday for the 31st in addition to the 29th and 30th.
        got = cronex.annotate(2016, 1, 29)
        expected_subset = set([(XW, 29), (XW, 30), (XW, 31)])
        intersection = got.intersection(expected_subset)
        self.assertEqual(expected_subset, intersection)

        # The first day of October 2016 is a Saturday, so the 3rd is annotated
        # as the nearest weekday for the 1st in addition to the 2nd and 3rd.
        # annotated as the nearest week day for the 30th and 31st.
        got = cronex.annotate(2016, 10, 3)
        expected_subset = set([(XW, 1), (XW, 2), (XW, 3)])
        intersection = got.intersection(expected_subset)
        self.assertEqual(expected_subset, intersection)


class TestDynamicExpressionTranslation(TestCase):
    def test_as_annotation_nth_dotw(self):
        # Reject invalid day of the week
        self.assertRaises(cronex.OutOfBounds,
            cronex.as_annotation, cronex.FIELD_DOTW, "8#1"
        )

        # Reject invalid counter values.
        self.assertRaises(cronex.OutOfBounds,
            cronex.as_annotation, cronex.FIELD_DOTW, "1#0"
        )
        self.assertRaises(cronex.OutOfBounds,
            cronex.as_annotation, cronex.FIELD_DOTW, "1#6"
        )

        # Nth day of the week should only work with the days-of-the-week field.
        for field in cronex.FIELDS:
            if field == cronex.FIELD_DOTW:
                continue
            self.assertRaises(cronex.InvalidUsage,
                cronex.as_annotation, field, "1#1"
            )

        # Verify that valid counts and days of the week are accepted.
        for dotw in range(7):
            for count in range(1, 6):
                atom = "%d#%d" % (dotw, count)
                with self.non_fatal_exception():
                    cronex.as_annotation(cronex.FIELD_DOTW, atom)

    def test_as_annotation_last_occurence_of_a_dotw(self):
        self.assertRaises(cronex.OutOfBounds,
            cronex.as_annotation, cronex.FIELD_DOTW, "99L"
        )

        for field in cronex.FIELDS:
            if field == cronex.FIELD_DOTW:
                continue
            self.assertRaises(cronex.InvalidUsage,
                cronex.as_annotation, field, "1L"
            )

        for n in range(1, 6):
            with self.non_fatal_exception():
                cronex.as_annotation(cronex.FIELD_DOTW, "%dL" % (n, ))

    def test_as_annotation_last_day(self):
        # The last-day symbol only works in the days-of-the-week and
        # days-of-the-month fields.
        for field in cronex.FIELDS:
            if field in (cronex.FIELD_DAYS, cronex.FIELD_DOTW):
                continue
            self.assertRaises(cronex.InvalidUsage,
                cronex.as_annotation, field, "L"
            )

        # L in days field represents 0 days until the end of the month.
        expected = (cronex.ANNOTATION_L_LX, 0)
        got = cronex.as_annotation(cronex.FIELD_DAYS, "L")
        self.assertEqual(expected, got)

        # L in days of the week field represents Saturday, but it should be
        # converted to a number further up the stack.
        self.assertRaises(cronex.Error,
            cronex.as_annotation, cronex.FIELD_DOTW, "L"
        )

    def test_as_annotation_days_before_end_of_month(self):
        # Days before the end of the month is only valid in the
        # days-of-the-month field.
        for field in cronex.FIELDS:
            if field == cronex.FIELD_DAYS:
                continue
            self.assertRaises(cronex.InvalidUsage,
                cronex.as_annotation, field, "L-1"
            )

        # Longest month has 31 days, so maximum number of days before end of
        # month is 30.
        self.assertRaises(cronex.OutOfBounds,
            cronex.as_annotation, cronex.FIELD_DAYS, "L-31"
        )

        for remaining_days in range(31):
            expected = (cronex.ANNOTATION_L_LX, remaining_days)
            got = cronex.as_annotation(cronex.FIELD_DAYS, "L-%d" % remaining_days)
            self.assertEqual(expected, got)

    def test_as_annotation_nearest_weekday(self):
        # The nearest weekday is only valid in the days-of-the-month field.
        for field in cronex.FIELDS:
            if field == cronex.FIELD_DAYS:
                continue
            self.assertRaises(cronex.InvalidUsage,
                cronex.as_annotation, field, "1W"
            )

        for day in range(1, 32):
            with self.non_fatal_exception():
                cronex.as_annotation(cronex.FIELD_DAYS, "%dW" % (day, ))

        for day in (0, 32):
            self.assertRaises(cronex.OutOfBounds,
                cronex.as_annotation, cronex.FIELD_DAYS, "%dW" % (day, )
            )


class TestfixedConstraintExpansion(TestCase):
    def test_expand_expression_validation(self):
        for field in cronex.FIELDS:
            minimum, maximum = cronex.FIELD_RANGES[field]

            with self.non_fatal_exception():
                cronex.expand(field, str(minimum))

            with self.non_fatal_exception():
                cronex.expand(field, str(maximum))

            self.assertRaises(cronex.OutOfBounds,
                cronex.expand, field, str(maximum + 1)
            )

            self.assertRaises(cronex.OutOfBounds,
                cronex.expand, field, "%s-%s" % (minimum, maximum + 1)
            )

            if minimum < 1:
                continue

            self.assertRaises(cronex.OutOfBounds,
                cronex.expand, field, str(minimum - 1)
            )
            self.assertRaises(cronex.OutOfBounds,
                cronex.expand, field, "%s-%s" % ((minimum - 1), maximum)
            )

        # The step size must be greater than 0.
        self.assertRaises(cronex.InvalidField,
            cronex.expand, cronex.FIELD_YEARS, "1970-2000/0"
        )

        self.assertRaises(cronex.FieldSyntaxError,
            cronex.expand, cronex.FIELD_YEARS, "X"
        )

    def test_expand_successful_evaluation(self):
        test_cases = [
            (cronex.FIELD_DAYS,     "1-31/1", range(1, 32)),
            (cronex.FIELD_DAYS,     "1-31",   range(1, 32)),
            (cronex.FIELD_DAYS,     "1-31/2", (1, 3, 5, 7, 9, 11, 13, 15, 17,
                                               19, 21, 23, 25, 27, 29, 31)),
            (cronex.FIELD_DOTW,     "5-1/3",  (5, 1)),
            (cronex.FIELD_DOTW,     "0",      (0, )),
            (cronex.FIELD_MINUTES,  "5-9/30", (5, )),
        ]

        for field, expression, expected in test_cases:
            expected = frozenset(expected)
            got = cronex.expand(field, expression)
            self.assertEqual(expected, got)


class TestFieldSplitting(TestCase):
    def test_atomize_input_validation(self):
        for field in cronex.FIELDS:
            # No fields may be empty.
            self.assertRaises(cronex.FieldSyntaxError,
                cronex.atomize, field, ""
            )

            # Multiple asterisks in one field are invalid.
            self.assertRaises(cronex.InvalidUsage,
                cronex.atomize, field, "*,*"
            )

            # Multiple question marks in one field are invalid.
            self.assertRaises(cronex.InvalidUsage,
                cronex.atomize, field, "?,?"
            )

    def test_atomize_month_replacement(self):
        test_cases = [
            ("Jan,FEB,mar,12", ("1", "2", "3", "12")),
            ("aPr,MAy,Jun,12", ("4", "5", "6", "12")),
            ("jul,aug,SEP,12", ("7", "8", "9", "12")),
            ("oct,NOV,dec,1",  ("10", "11", "12", "1")),
        ]

        for expression, expected in test_cases:
            self.assertReturns(set(expected),
                cronex.atomize, cronex.FIELD_MONTHS, expression
            )

    def test_atomize_dotw_replacement(self):
        test_cases = [
            ("sun,MoN,tue,6", ("0", "1", "2", "6")),
            ("wed,thu,Fri,1", ("3", "4", "5", "1")),
            ("Sat,0,1",       ("6", "0", "1")),
            ("L,1,L-1",       ("0", "1", "L-1")),
        ]

        for expression, expected in test_cases:
            self.assertReturns(set(expected),
                cronex.atomize, cronex.FIELD_DOTW, expression
            )


class TestAtomicExpressionParsing(TestCase):
    def test_parse_atom_input_validation(self):
        epoch = cronex.Epoch(1970, 1, 1, 0)
        epoch_without_date = cronex.Epoch(None, None, None, 0)
        epoch_without_timestamp = cronex.Epoch(1970, 1, 1, None)

        self.assertRaises(cronex.InvalidField,
            cronex.parse_atom, cronex.FIELD_DOTW, "0-6", epoch
        )

        for field in cronex.FIELDS:
            # Question marks can only appear in days or days-of-the-week.
            if field not in (cronex.FIELD_DAYS, cronex.FIELD_DOTW):
                self.assertRaises(cronex.InvalidUsage,
                    cronex.parse_atom, field, "?", epoch
                )

            # Monotonic are not allowed in the days of the week.
            if field == cronex.FIELD_DOTW:
                self.assertRaises(cronex.InvalidUsage,
                    cronex.parse_atom, field, "%2", epoch
                )
                continue

            # A monotonic period of two should work in any field.
            with self.non_fatal_exception():
                cronex.parse_atom(field, "%2", epoch)

            # Monotonic periods must be greater than 1.
            self.assertRaises(cronex.OutOfBounds,
                cronex.parse_atom, field, "%1", epoch
            )

            # Monotonic periods must be an integer.
            self.assertRaises(cronex.FieldSyntaxError,
                cronex.parse_atom, field, "%X", epoch
            )

            if (field in
              (cronex.FIELD_YEARS, cronex.FIELD_MONTHS, cronex.FIELD_DAYS)):
                self.assertRaises(cronex.FieldSyntaxError,
                    cronex.parse_atom, field, "%2", epoch_without_date
                )

            elif (field in
              (cronex.FIELD_HOURS, cronex.FIELD_MONTHS, cronex.FIELD_SECONDS)):
                self.assertRaises(cronex.FieldSyntaxError,
                    cronex.parse_atom, field, "%2", epoch_without_timestamp
                )

    def test_parse_atom_dotw_fixed_expansion(self):
        with mock(cronex, "expand", value=(0, 1, 2)) as proxy:
            self.assertReturns((
                cronex.EXPRESSION_ANNOTATED,
                frozenset([
                    (cronex.ANNOTATION_DOTW, 0),
                    (cronex.ANNOTATION_DOTW, 1),
                    (cronex.ANNOTATION_DOTW, 2),
                ])),
                cronex.parse_atom, cronex.FIELD_DOTW, "0-2", None
            )

            self.assertEqual([((cronex.FIELD_DOTW, "0-2"), {})], proxy.calls)

    def test_parse_atom_fixed_expansion(self):
        with mock(cronex, "expand", value="Y") as proxy:
            for field in cronex.FIELDS:
                if field == cronex.FIELD_DOTW:
                    continue

                proxy.reset()
                sentinel = "X" + str(field)
                self.assertReturns((cronex.EXPRESSION_FIXED, "Y"),
                    cronex.parse_atom, field, sentinel, None
                )
                self.assertEqual([((field, sentinel), {})], proxy.calls)

        # Verify that "?" is converted to "*" in the days of the week field.
        with mock(cronex, "expand", value="Y") as proxy:
            self.assertReturns((cronex.EXPRESSION_FIXED, "Y"),
                cronex.parse_atom, cronex.FIELD_DAYS, "?", None
            )
            self.assertEqual([((cronex.FIELD_DAYS, "*"), {})], proxy.calls)

    def test_parse_atom_dynamic_day_annotation(self):
        class RegexMock(object):
            @classmethod
            def match(cls, *args, **kwargs):
                return True

        with mock(cronex, "ANNOTATABLE_FIELD_REGEX", value=RegexMock):
            with mock(cronex, "as_annotation", value="X") as f:
                self.assertReturns((cronex.EXPRESSION_ANNOTATED, set(["X"])),
                    cronex.parse_atom, cronex.FIELD_DAYS, "Y", None
                )
                self.assertEqual([((cronex.FIELD_DAYS, "Y"), {})], f.calls)

    def test_parse_atom_monotonic_to_fixed_months(self):
        test_cases = [
            ((1, 7),        "%6",   cronex.Epoch(2000, 1, 1, None)),
            ((2, 8),        "%6",   cronex.Epoch(2000, 2, 1, None)),
            ((5, 8, 11, 2), "%3",   cronex.Epoch(2020, 5, 1, None)),
            ((3, ),         "%12",  cronex.Epoch(2020, 3, 1, None)),
        ]

        for expected, expression, epoch in test_cases:
            self.assertReturns((cronex.EXPRESSION_FIXED, set(expected)),
                cronex.parse_atom, cronex.FIELD_MONTHS, expression, epoch
            )

    def test_parse_atom_monotonic_to_fixed_years(self):
        test_cases = [
            ((2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000),
                            "%1000",    cronex.Epoch(2000, 1, 1, None)),
            ((2100, 8100),  "%6000",    cronex.Epoch(2100, 1, 1, None)),
            ((2200, 7200),  "%5000",    cronex.Epoch(2200, 1, 1, None)),
        ]

        for expected, expression, epoch in test_cases:
            self.assertReturns((cronex.EXPRESSION_FIXED, set(expected)),
                cronex.parse_atom,
                    cronex.FIELD_YEARS, expression, epoch
            )

    def test_parse_atom_monotonic_to_fixed_seconds(self):
        E = lambda t: cronex.Epoch(None, None, None, t)
        test_cases = [
            ((5, 15, 25, 35, 45, 55),   "%10",    E(65)),  # 00:01:05
            ((40, 55, 10, 25),          "%15",    E(100)), # 00:01:40
            ((30, ),                    "%60",    E(90)),  # 00:01:30
        ]

        for expected, expression, epoch in test_cases:
            self.assertReturns((cronex.EXPRESSION_FIXED, set(expected)),
                cronex.parse_atom,
                    cronex.FIELD_SECONDS, expression, epoch
            )

    def test_parse_atom_monotonic_fallthrough(self):
        epoch = cronex.Epoch(1970, 1, 1, 0)

        for field in cronex.FIELDS:
            if field in (cronex.FIELD_YEARS, cronex.FIELD_DOTW):
                continue
            # 7 is co-prime to the ends of the ranges of all fields, so it
            # should never be converted to a fixed expression.
            self.assertReturns((cronex.EXPRESSION_MONOTONIC, 7),
                cronex.parse_atom, field, "%7", epoch
            )


class TestConstraintGeneration(TestCase):
    def test_generate_expression_sets(self):
        pass


class TestCronExpression(TestCase):
    def test_field_count_validation(self):
        with mock(cronex, "generate_expression_sets"):
            self.assertRaises(cronex.MissingFieldsError,
                cronex.CronExpression, "* * * *"
            )

            self.assertRaises(cronex.MissingFieldsError,
                cronex.CronExpression, "* * * * *", with_seconds=True
            )

            self.assertRaises(cronex.MissingFieldsError,
                cronex.CronExpression, "* * * * *", with_years=True
            )

            self.assertRaises(cronex.MissingFieldsError,
                cronex.CronExpression,
                    "* * * * * *", with_seconds=True, with_years=True
            )

    def test_expression_and_comment_property_assignment(self):
        test_cases = [
            (("A B C D E", "XYZ PQR"), ("A   B C D E           XYZ PQR", )),
            (("A B C D E", "AAA ZZZ"), ("A B   C D E           AAA ZZZ  ", )),
            (("A B C D E", "111 999"), ("A B C D   E         111 999  ", )),
            (("A B C D E", ""),        ("A B C D   E  ", )),
            (("A B C D E", ""),        ("  A B C D E     ", )),
            (("@annually", "XYZ   P"), ("@annually       XYZ   P  ", )),
            (("@daily", "QQQ WWW"),    ("@daily       QQQ WWW  ", )),
        ]

        with mock(cronex, "generate_expression_sets"):
            for (expected_expression, expected_comment), args in test_cases:
                c = cronex.CronExpression(*args)
                self.assertEqual(expected_expression, c.expression)
                self.assertEqual(expected_comment, c.comment)

                if "@" not in str(args):
                    continue

                # Whether or not with_seconds and with_years are set should not
                # change the comment or expression for substitutions.
                c = cronex.CronExpression(*args, with_seconds=True,
                    with_years=True)
                self.assertEqual(expected_expression, c.expression)
                self.assertEqual(expected_comment, c.comment)

    def test_equality(self):
        a = cronex.CronExpression("* * * * *", cronex.Epoch(1970, 1, 1, 0))
        self.assertNotEqual(a, "a")
        self.assertEqual(a, a)

        a2 = cronex.CronExpression("* * * * *", cronex.Epoch(1970, 1, 1, 0))
        self.assertEqual(a2, a2)
        self.assertEqual(a, a2)

        b = cronex.CronExpression("0 0 * * *", cronex.Epoch(1970, 1, 1, 0))
        self.assertEqual(b, b)
        self.assertNotEqual(a, b)
        self.assertNotEqual(a2, b)

        # The epoch shouldn't affect equality when there are no monotonic
        # expressions.
        b2 = cronex.CronExpression(
            "0 0 * * *", cronex.Epoch(2000, 12, 31, 999999))
        self.assertEqual(b2, b2)
        self.assertEqual(b, b2)

        b3 = cronex.CronExpression(
            "0 0 * * *", cronex.Epoch(1999, 1, 1, 1234567))
        self.assertEqual(b3, b3)
        self.assertNotEqual(a, b3)

        # The Y-M-D epoch should be ignored if there are no monotonic
        # expressions for the month and day.
        c = cronex.CronExpression(
            "%91 * * * *", cronex.Epoch(1999, 1, 1, 3333))
        self.assertEqual(c, c)
        self.assertNotEqual(a, c)

        c2 = cronex.CronExpression(
            "%91 * * * *", cronex.Epoch(2020, 9, 6, 3333))
        self.assertEqual(c2, c2)
        self.assertEqual(c, c2)

        d = cronex.CronExpression(
            "* %91 * * *", cronex.Epoch(1999, 1, 1, 3333))
        self.assertEqual(d, d)
        self.assertNotEqual(a, d)

        d2 = cronex.CronExpression(
            "* %91 * * *", cronex.Epoch(2020, 9, 6, 3333))
        self.assertEqual(d2, d2)
        self.assertEqual(d, d2)

        e = cronex.CronExpression(
            "%91 * * * * *", cronex.Epoch(1999, 1, 1, 3333), with_seconds=True)
        self.assertEqual(e, e)
        self.assertNotEqual(a, e)

        e2 = cronex.CronExpression(
            "%91 * * * * *", cronex.Epoch(2020, 9, 6, 3333), with_seconds=True)
        self.assertEqual(e2, e2)
        self.assertEqual(e, e2)

        # The epoch timestamp should be ignored if there are no monotonic
        # expressions for the minute, second and hour.
        f = cronex.CronExpression(
            "* * %91 * *", cronex.Epoch(1999, 1, 1, 1111111))
        self.assertEqual(f, f)
        self.assertNotEqual(a, f)

        f2 = cronex.CronExpression(
            "* * %91 * *", cronex.Epoch(1999, 1, 1, 2222222))
        self.assertEqual(f2, f2)
        self.assertEqual(f, f2)

        g = cronex.CronExpression(
            "* * * %91 *", cronex.Epoch(1999, 1, 1, 1111111))
        self.assertEqual(g, g)
        self.assertNotEqual(a, g)

        g2 = cronex.CronExpression(
            "* * * %91 *", cronex.Epoch(1999, 1, 1, 2222222))
        self.assertEqual(g2, g2)
        self.assertEqual(g, g2)

        # The entire epoch matters in other cases.
        h = cronex.CronExpression(
            "%91 %91 %91 * *", cronex.Epoch(1999, 1, 1, 1111111))
        self.assertEqual(h, h)
        self.assertNotEqual(a, h)

        k = cronex.CronExpression(
            "%91 %91 %91 * *", cronex.Epoch(2038, 3, 2, 1111111))
        self.assertEqual(k, k)
        self.assertNotEqual(h, k)

        m = cronex.CronExpression(
            "%91 %91 %91 * *", cronex.Epoch(1999, 1, 1, 222222222))
        self.assertEqual(m, m)
        self.assertNotEqual(h, m)

    def test_repr_and_str(self):
        test_cases = [
            "* * * * *",
            "*/5 0 * * *",
            "*/15 20 1 1 1",
            "*/15 %30 * * *",
            "*/45 %5,%45,%30 * * *",
            "5-45/7 %11 * * *",
        ]

        # Needed for eval to work.
        CronExpression = cronex.CronExpression
        Epoch = cronex.Epoch

        epoch = cronex.Epoch(1970, 1, 1, 0)
        for expression in test_cases:
            a = cronex.CronExpression(expression, epoch=epoch)
            b = eval(repr(a))
            self.assertFalse(a is b)
            self.assertEqual(a, b)
            self.assertEqual(repr(a), repr(b))
            self.assertEqual(str(a), str(b))


@contextlib.contextmanager
def mock(owner, name, value=None):
    """
    Simple context manager for mocking out properties.

    Arguments:
    - owner (object): Object that possesses the attribute to be mocked.
    - name (str): Name of the attribute to be mocked.
    - value: If the attribute is a callable, this is the value the mock
      function returns when called. Otherwise, this is the new value of the
      mocked property.

    Returns: The new callable or the replacement value. If the mocked property
    was a callable, the returned function has three attributes: "calls", a list
    of (*arg, **kwarg) pairs representing calls to the mocked function; "call",
    shorthand for `calls[-1]`; "called", shorthand for `bool(calls)` and
    "reset", a function that resets the aforementioned values.
    """
    original = getattr(owner, name)

    if callable(original):
        def replacement(*args, **kwargs):
            parameters = (args, kwargs)
            replacement.calls.append(parameters)
            replacement.call = parameters
            replacement.called = True
            return value

        def reset():
            replacement.calls = list()
            replacement.call = None
            replacement.called = False

        replacement.reset = reset
        replacement.reset()

    else:
        replacement = value

    try:
        setattr(owner, name, replacement)
        yield replacement
    finally:
        setattr(owner, name, original)


if __name__ == "__main__":
    cronex.unittestmixins.main()
