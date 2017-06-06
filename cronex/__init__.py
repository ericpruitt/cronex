#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time

DYNAMIC_FIELD_MATCHERS = [
    "L",
    "L-[0-9]+",
    "[0-9]+#[0-9]+",
    "[0-9]+L",
    "[0-9]+W",
]

SUBSTITUTIONS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *"
}

ORDERED_FIELD_RANGES_AND_NAMES = (
    ("seconds",                (0,   59)),
    ("minutes",                (0,   59)),
    ("hours",                  (0,   23)),
    ("days",                   (1,   31)),
    ("months",                 (1,   12)),
    ("days_of_the_week",       (0,    6)),
    ("years",               (1970, 9999)),
)
FIELD_NAMES = tuple((name for name, _ in ORDERED_FIELD_RANGES_AND_NAMES))
FIELD_RANGES = dict(ORDERED_FIELD_RANGES_AND_NAMES)

ASTERISK = frozenset(range(max(0, 10000)))

DAY_MAP = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6
}
MONTH_MAP = {
    "JAN":  1,  "FEB":  2,  "MAR":  3,  "APR":  4,  "MAY":  5,  "JUN":  6,
    "JUL":  7,  "AUG":  8,  "SEP":  9,  "OCT": 10,  "NOV": 11,  "DEC": 12,
}

DAY_REGEX = re.compile(r"\b(%s)L?\b" % "|".join(DAY_MAP.keys()), re.I)
MONTH_REGEX = re.compile(r"\b(%s)\b" % "|".join(MONTH_MAP.keys()), re.I)

DYNAMIC_DOTW = "?"
DYNAMIC_L_LX = "L/L-?"
DYNAMIC_XHX = "?#?"
DYNAMIC_XL = "?L"
DYNAMIC_XW = "?W"

DYNAMIC_FIELD_REGEX = re.compile("(%s)$" % "|".join(DYNAMIC_FIELD_MATCHERS))
RANGE_REGEX = re.compile("((?P<first>\d+)-(?P<last>\d+)|\*)(/(?P<step>\d+))?$")


class Error(Exception):
    """
    Module-specific base exception class.
    """


class InvalidField(Error):
    """
    Exception raised when a field in an expression could not be processed for
    any reason.
    """

    def __init__(self, field, problem):
        """
        Arguments:
        - field: name of the field containing the error.
        - problem: text describing why the field is invalid.
        """
        self.field = field
        self.problem = problem

    def __str__(self):
        field_display_name = self.field.replace("_", " ")
        return "Invalid %s: %s" % (field_display_name, self.problem)

    def __repr__(self):
        return "%s(%r, %r)" % (self.field, self.problem)


class MisingFieldsError(Error):
    """
    Exception raised when there are too few fields specified in the constructor
    CronExpression.
    """


class FieldSyntaxError(InvalidField):
    """
    Exception raised when a field is syntactically invalid.
    """


class InvalidUsage(InvalidField):
    """
    Exception raised when an expression is syntactically valid but cannot be
    used in the field where it appears.
    """


class OutOfBounds(InvalidField):
    """
    Exception raised when a number is outside of permitted bounds.
    """

    @classmethod
    def check(cls, field, what, expression=None):
        """
        Check to see if a value or values are outside the range of valid values
        for a particular field.

        Arguments:
        - field: name of the field.
        - what: either a single integer or an iterable with an arbitrary number
          of integers to validate. If only some of the values are out of
          bounds, the exception message will only mention those numbers.
        - expression: option text that represents the expression being
          validated. If the this text represents a single number with the same
          value as the "what" argument, it is ignored so the same number is not
          displayed twice in the exception message.
        """
        try:
            values = set(what)
        except TypeError:
            values = set([what])

        minimum, maximum = FIELD_RANGES[field]
        values = set((v for v in values if not (minimum <= v <= maximum)))

        if not values:
            return

        try:
            if len(values) == 1 and (int(expression) in values or
              float(expression) in values):
                expression = None
        except ValueError:
            pass

        parts = (
            "valid values are %s ≤ n ≤ %s, but" % (minimum, maximum),
            "'%s'" % expression if expression else "field",
            "includes",
            ", ".join(map(str, values)),
        )
        problem = " ".join(parts)

        raise cls(field, problem)


class CronExpression(object):
    def __init__(self, text, epoch=None, epoch_utc_offset=None,
      with_seconds=False, with_years=False):
        """
        Instantiate a CronExpression object with an optionally defined epoch.
        If the epoch is defined, the UTC offset can be specified one of two
        ways: as the sixth element in 'epoch' or supplied in epoch_utc_offset.
        The epoch should be defined down to the minute sorted by descending
        significance.

        Arguments:
        - text: expression to parse. This must contain at least 5 fields but 6
          and 7 are also allowed depending on whether or not "with_seconds" and
          "with_years" are True.
        - epoch: either a Unix timestamp or a tuple with a date and optionally
          time that represents the starting point of all monotonic constraints.
          The epoch may be defined with any iterable, but if the object has the
          attribute "tm_gmtoff", it will be handled appropriately unless
          "epoch_utc_offset" is set.
        - epoch_utc_offset: offset of the epoch in seconds east of UTC. If this
          value is not None, it takes precedence over `epoch.tm_gmtoff`.
        """
        original_text = text
        text = text.lstrip()
        self.comment = ""

        for key, value in SUBSTITUTIONS.items():
            if text.startswith(key):
                if with_seconds:
                    value = "0 " + value
                if with_years:
                    value += " *"
                text = text.replace(key, value)
                break

        expected_fields = 5 + with_seconds + with_years
        columns = text.split(None, expected_fields)
        colcount = len(columns)

        if colcount < expected_fields:
            raise MisingFieldsError(
                "Need %d fields but found %d" % (expected_fields, colcount)
            )

        if colcount > expected_fields:
            self.comment = columns.pop()

        if not with_seconds:
            columns.insert(0, "*")

        if not with_years:
            columns.append("*")

        if epoch is not None:
            if isinstance(epoch, int):
                year, month, day = time.localtime(epoch)[:3]
            else:
                year, month, day = epoch[:3]

            self.epoch_unixtime = time.mktime(epoch)
            self.epoch_ordinal_months = year * 12 + month - 1

        self.epoch = epoch
        self.epoch_utc_offset = epoch_utc_offset
        self.with_seconds = with_seconds
        self.with_years = with_years

        try:
            self._fixed, self._dynamic, self._monotonic = parse(columns)
        except Error as e:
            raise Error("%s: %s" % (original_text, e))

        self._need_seconds_delta = any((
            self._monotonic["days"],
            self._monotonic["minutes"],
            self._monotonic["seconds"],
        ))

    def __eq__(self, other):
        """
        Two CronExpression instances are considered equivalent based on
        scheduling even if the original text input differed;
        `CronExpression("*/30 0,8,16 * Sun,Wed *")` is considered equal to
        `CronExpression("0,30 */8 * 0,3 *")`.
        """
        return (
            self._fixed == other._fixed and
            self._dynamic == other._dynamic and
            self._monotonic == other._monotonic
        )

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        original_value = self._text
        try:
            self.__init__(
                text=value,
                epoch=self.epoch,
                epoch_utc_offset=self.epoch_utc_offset,
                with_seconds=self.with_seconds,
                with_years=self.with_years,
            )
        except:
            self._text = original_value
            raise

    def check_trigger(self, when=None):
        months_delta = 0
        second = 0
        seconds_delta = 0

        if when is None or isinstance(when, int):
            year, month, day, hour, minute, second = time.localtime(when)[:6]
        elif self.with_seconds:
            year, month, day, hour, minute, second = when[:6]
        else:
            year, month, day, hour, minute = when[:5]

        if self._need_seconds_delta:
            if isinstance(when, int):
                unixtime = when
            else:
                instant = (year, month, day, hour, minute, second, 0, 0, -1)
                unixtime = time.mktime(instant)

            seconds_delta =  self.epoch_unixtime

        if self._monotonic["months"]:
            ordinal_months = year * 12 + month - 1
            months_delta = ordinal_months - self.epoch_ordinal_months

        if (hour not in self._fixed["hours"] and
          not check_monotonic(seconds_delta, self._monotonic["hours"], 3600)):
            return False

        if (minute not in self._fixed["minutes"] and
          not check_monotonic(seconds_delta, self._monotonic["minutes"], 60)):
            return False

        if (month not in self._fixed["months"] and
          not check_monotonic(months_delta, self._monotonic["months"])):
            return False

        if (second not in self._fixed["seconds"] and
          not check_monotonic(seconds_delta, self._monotonic["seconds"])):
            return False

        if (day not in self._fixed["days"] and not self._dynamic or
          not annotate(year, month, day).issuperset(self._dynamic)):
            return False

        if year not in self._fixed["years"]:
            return False

        return True


def dotw_7to0(x):
    """
    Helper function to convert 7 to 0 for values that represent days of the
    week.
    """
    return 0 if x == 7 else x


def translate(field, expression):
    """
    Convert an expression for a dynamic condition into an annotation.
    """
    if "#" in expression:
        day_of_the_week, value = map(int, expression.split("#", 1))
        day_of_the_week = dotw_7to0(day_of_the_week)
        OutOfBounds.check(field, day_of_the_week, expression)

        if value < 1 or value > 5:
            raise OutOfBounds(field,
                "the week number must be greater than or equal to 1 and less"
                " than or equal to 5 (found %d in %s)" % (value, expression)
            )

        if field != "days_of_the_week":
            raise InvalidUsage(field,
                "Nth occurrence of a day of the week (%s) is only valid in the"
                " days of the week field" % (expression, )
            )

        return (DYNAMIC_XHX, day_of_the_week, value)

    if expression == "L":
        if field not in ("days", "days_of_the_week"):
            raise InvalidUsage(field,
                "'L' is only applicable to the days (last day of the"
                " month) and days of the week (last day of the week;"
                " always Saturday) fields"
            )

        return (DYNAMIC_L_LX, 0)

    if expression.startswith("L-"):
        distance = int(expression.split("-")[1])

        if distance > 30:
            raise OutOfBounds(field,
                "the longest months have 31 days, so %d days before the end of"
                " the month is invalid" % (distance, )
            )

        if field != "days":
            raise InvalidUsage(field,
                "days before the end of the month (%r) is only applicable"
                " to the days field" % (expression, )
            )

        return (DYNAMIC_L_LX, distance)

    if expression.endswith("L"):
        day_of_the_week = dotw_7to0(int(expression[:-1]))
        OutOfBounds.check(field, day_of_the_week, expression)

        if field != "days_of_the_week":
            day_name = DAYS_OF_THE_WEEK[day_of_the_week]
            raise InvalidUsage(field,
                "last occurrence of %s (%s) is only applicable to the days"
                " of the week field" % (expression, day_name)
            )

        return (DYNAMIC_XL, day_of_the_week)

    if expression.endswith("W"):
        day = int(expression[:-1])
        OutOfBounds.check(field, day, expression)
        return (DYNAMIC_XW, day)


def check_monotonic(value, series, numerator=0):
    """
    Check to see if a value is a multiple of any numbers in the series. The
    value is divided by the numerator when the numerator is a non-zero value.

    Arguments:
    - value: number 
    - series: set of numbers representing monotonic periods.
    - numerator: when non-zero, the value is divided by this number before
      checking for membership in the series.

    Returns: boolean True or False indicating membership.
    """
    if series and value:
        if numerator:
            value //= numerator

        for item in series:
            if not (value % item):
                return True

    return False


def annotate(year, month, day):
    """
    Return a set of annotations that apply to the given date. If a date is
    invalid, None is returned.

    Arguments:
    - year: integer representing the date's year.
    - month: integer representing the date's month.
    - day: integer representing the day of the month.

    Returns: a frozenset containing applicable annotations.
    """
    if month in (1, 3, 5, 7, 8, 10, 12):
        last_day_of_month = 31
    elif month in (4, 6, 9, 11):
        last_day_of_month = 30
    elif month == 2:
        last_day_of_month = 28 + (
            not (year % 4) and (year % 100 or not (year % 400))
        )

    y = (year - 1) if month < 3 else year
    dow = 23 * month // 9 + day + 4 + year + y // 4 - y // 100 + y // 400

    if month >= 3:
        dow -= 2
    dow %= 7

    annotations = [
        (DYNAMIC_L_LX, last_day_of_month - day),
        (DYNAMIC_XHX, dow, day // 7 + 1),
        (DYNAMIC_DOTW, dow),
    ]

    if (last_day_of_month - day) < 7:
        annotations.append((DYNAMIC_XL, dow))

    if 1 <= dow <= 5:
        annotations.append((DYNAMIC_XW, day))

        if dow == 1:
            # Sunday -> Monday
            if day > 1:
                annotations.append((DYNAMIC_XW, day - 1))
            # Saturday --(+2d)-> Monday because Friday is in a different month
            if day == 3:
                annotations.append((DYNAMIC_XW, day - 2))
        elif dow == 5:
            # Friday <- Saturday
            if day < last_day_of_month:
                annotations.append((DYNAMIC_XW, day + 1))
            # Friday <-(-2d)-- Sunday because Monday is in a different month
            if (day + 2) > last_day_of_month:
                annotations.append((DYNAMIC_XW, day + 2))

    return frozenset(annotations)


def expand(field, expression):
    """
    Convert an expression for a fixed condition into a series of numbers.

    In Vixie cron, using a step with a range that is too large results in a
    range expanding to a single value, e.g.: "5-15/30" is effectively the same
    as "5". For the sake of compatibility, this function handle steps the same
    way.

    Arguments:
    - field: name of the field in which expansion is taking place.
    - expression: expression in the form of "A" (single number), "A-B" (list of
      values from A to B, inclusive), "A-B/X" (like "A-B" but in increments of
      X) or "*/X" (every value in increments of "X"). If "A" is greater than
      "B", the list will wrap around; for example, "23-3" in the hour field
      expands to {23, 0, 1, 2, 3}.

    Returns: a frozenset containing all values enumerated by the expression.
    """
    if expression.isdigit():
        value = int(expression)
        OutOfBounds.check(field, value, expression)
        return frozenset((value, ))

    match = RANGE_REGEX.match(expression)

    if not match:
        raise FieldSyntaxError(field,
            "'%s' is not a valid number or range expression" % (expression, )
        )

    step = int(match.group("step") or 1)

    if step < 1:
        raise InvalidField(field, "step size must be greater than 0")

    fmin, fmax = FIELD_RANGES[field]
    first = int(match.group("first") or fmin)
    last = int(match.group("last") or fmax)

    if field == "days_of_the_week":
        first = (0 if first == 7 else first)
        last = (0 if last == 7 else last)

    OutOfBounds.check(field, (first, last), expression)

    if first < last:
        return frozenset(range(first, last + 1, step))

    elements = list()
    elements.extend(range(first, fmax + 1))
    elements.extend(range(fmin, last + 1))
    return frozenset(elements[::step])


def simplify_monotonic_series(values):
    """
    Remove redundant numbers from a set of monotonic periods. For example, in
    the set {5, 17, 25, 45}, the numbers 25 and 45 are redundant because they
    are both multiples of 5, so this function would return {5, 17}.
    """
    if len(values) < 2:
        return values

    factors = set()
    for value in sorted(values):
        if not factors:
            factors.add(value)
            continue

        for factor in factors:
            if not (value % factor):
                break
        else:
            factors.add(value)

    return frozenset(factors)


def parse(fields, epoch=None):
    """
    Parse and convert a series textual cron fields into machine-friendly
    representations of static, dynamic and monotonic constraints.

    Unlike Vixie cron, this function allows the use of month names and day
    names in any context including ranges and lists.
    """
    dynamic = set()
    monotonic = dict((name, set()) for name in FIELD_NAMES)
    static = dict((name, set()) for name in FIELD_NAMES)

    day_replacer = lambda match: str(DAY_MAP[match.string.upper()])
    month_replacer = lambda match: str(MONTH_MAP[match.string.upper()])

    for field, contents in zip(FIELD_NAMES, fields):
        if contents == "?" and field not in ("days", "days_of_the_week"):
            raise InvalidUsage(field,
                "'?' can only appear in the days or days of the week fields"
            )

        if contents in ("*", "?"):
            static[field] = ASTERISK
            continue

        atoms = contents.split(",")

        if "*" in atoms:
            raise InvalidUsage(field, "'*' must be the only value in a field")

        if "?" in atoms:
            raise InvalidUsage(field, "'?' must be the only value in a field")

        # Replace 3-letter abbreviations of days of the week and months
        # with numbers.
        if field == "days_of_the_week":
            contents = DAY_REGEX.sub(day_replacer, contents)

        elif field == "months":
            contents = MONTH_REGEX.sub(month_replacer, contents)

        for atom in set(atoms):
            if not atom:
                raise FieldSyntaxError(field,
                    "%s contains empty an expression" % (contents, )
                )
            if DYNAMIC_FIELD_REGEX.match(atom):
                dynamic.add(translate(field, atom))

            elif atom.startswith("%"):
                if field == "days_of_the_week":
                    raise InvalidUsage(field,
                        "monotonic constraints cannot be used in the days of"
                        "the week field"
                    )

                try:
                    period = int(atom[1:])
                except ValueError:
                    raise FieldSyntaxError(field,
                        "expected integer after %% in '%s'" % (atom, )
                    )

                if period < 2:
                    raise OutOfBounds(field, "period must be greater than 1")

                # Convert monotonic constraints to static constraints where
                # possible.
                if field == "months" and not (12 % period):
                    delta = epoch[3] - 1
                    count = 12 // period
                    static[field].update(
                        ((x * period + delta) % 12 + 1 for x in range(count))
                    )

                elif field == "seconds" and not (60 % period):
                    delta = epoch[5]
                    count = 60 // period
                    static[field].update(
                        ((x * period + delta) % 60 for x in range(count))
                    )

                elif field == "years":
                    _, year_max = FIELD_RANGES[field]
                    static[field].update(range(epoch[0], year_max + 1, period))

                else:
                    monotonic[field].add(period)

            elif field == "days_of_the_week":
                dotw_numbers = expand(field, atom)
                dynamic.update((DYNAMIC_DOTW, dotw) for dotw in dotw_numbers)

            else:
                static[field].update(expand(field, atom))

        # Any field with a set of static constraints that include all possible
        # values are replaced with ASTERISK references.
        begin, end = FIELD_RANGES[field]
        if len(static[field]) == (end - begin + 1):
            static[field] = ASTERISK

        # Delete redundant constraints in fields with static constraints that
        # are ASTERISK references.
        if static[field] is ASTERISK:
            monotonic[field] = frozenset()

        simplify_monotonic_series(monotonic[field])

    # The standard for cron implementations is that the day of the month and
    # the day of the week constraints trigger as a boolean OR condition when
    # both have an explicit value. When only one field has an explicit value,
    # the other is ignored. Since the trigger checking in this module is
    # implemented as (day_of_the_month_matches or day_of_the_week) matches, the
    # days field can be ignored by purging its constraints. Since the value of
    # static["days_of_the_week"] is never actually used and dynamic is empty by
    # default, nothing needs to be done for days of the week.
    if static["days"] is ASTERISK and dynamic:
        static["days"] = frozenset()

    return static, dynamic, monotonic
