#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import re
import time
# TODO: add tests for each member of ANNOTATABLE_PATTERNS

ANNOTATABLE_PATTERNS = [
    "L",
    "L-[0-9]+",
    "[0-9]+#[0-9]+",
    "[0-9]+L",
    "[0-9]+W",
]

SUBSTITUTIONS = {
    "@annually": "0 0 1 1 *",
    "@daily": "0 0 * * *",
    "@hourly": "0 * * * *",
    "@midnight": "0 0 * * *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@yearly": "0 0 1 1 *",
}

FIELD_SECONDS = "seconds"
FIELD_MINUTES = "minutes"
FIELD_HOURS = "hours"
FIELD_DAYS = "days"
FIELD_MONTHS = "months"
FIELD_DOTW = "days_of_the_week"
FIELD_YEARS = "years"

CONSTRAINT_ANNOTATION = "dynamic"
CONSTRAINT_MONOTONIC = "monotonic"
CONSTRAINT_FIXED = "fixed"

ORDERED_FIELD_RANGES_AND_NAMES = (
    (FIELD_SECONDS, (0,   59)),
    (FIELD_MINUTES, (0,   59)),
    (FIELD_HOURS,   (0,   23)),
    (FIELD_DAYS,    (1,   31)),
    (FIELD_MONTHS,  (1,   12)),
    (FIELD_DOTW,    (0,    6)),
    (FIELD_YEARS,   (1970, 9999)),
)
FIELDS = tuple((name for name, _ in ORDERED_FIELD_RANGES_AND_NAMES))
FIELD_RANGES = dict(ORDERED_FIELD_RANGES_AND_NAMES)

ASTERISK = frozenset(range(10000))

DAY_MAP = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
}
MONTH_MAP = {
    "JAN":  1,  "FEB":  2,  "MAR":  3,  "APR":  4,  "MAY":  5,  "JUN":  6,
    "JUL":  7,  "AUG":  8,  "SEP":  9,  "OCT": 10,  "NOV": 11,  "DEC": 12,
}

DAY_REGEX = re.compile(r"\b(%s)L?\b" % "|".join(DAY_MAP.keys()), re.I)
MONTH_REGEX = re.compile(r"\b(%s)\b" % "|".join(MONTH_MAP.keys()), re.I)

# TODO: Support for LW
ANNOTATION_DOTW = "?"
ANNOTATION_L_LX = "L/L-?"
ANNOTATION_XHX = "?#?"
ANNOTATION_XL = "?L"
ANNOTATION_XW = "?W"

ANNOTATABLE_FIELD_REGEX = re.compile("^(%s)$" % "|".join(ANNOTATABLE_PATTERNS))
RANGE_REGEX = re.compile("((?P<first>\d+)-(?P<last>\d+)|\*)(/(?P<step>\d+))?$")


class Epoch(
  collections.namedtuple("Epoch", ["year", "month", "day", "timestamp"])):
    """
    Date and / or time from which monotonic constraints begin counting.
    """


class Fields(collections.namedtuple("Fields", FIELDS)):
    """
    Collection of values associated with particular cron expression fields.
    """


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
        return "%s(%r, %r)" % (
            self.__class__.__name__, self.field, self.problem)


class MissingFieldsError(Error):
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

        Raises: OutOfBounds exception if one or more values are outside the
        valid range.
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
            # If the expression only contains one number, the expression is not
            # shown since it would be redundant.
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
    def __init__(self, text, epoch=Epoch(1970, 1, 1, 0), with_seconds=False,
      with_years=False):
        """
        Arguments:
        - text: expression to parse. This must contain at least 5 fields but 6
          and 7 are also allowed depending on whether or not "with_seconds" and
          "with_years" are True.
        - epoch: Epoch representing the date and / or time from which monotonic
          constraints begin counting.
        - with_seconds: Boolean value indicating whether or not the text
          expression includes a field for seconds.
        - with_years: Boolean value indicating whether or not the text
          expression includes a field for years.
        """
        parts = text.split(None, 1)
        expression, comment = parts if len(parts) == 2 else (parts, "")

        for target, replacement in SUBSTITUTIONS.items():
            if expression != target:
                continue

            if with_seconds:
                replacement = "0 " + replacement

            if with_years:
                replacement += " *"

            fields = replacement.split()
            break

        else:
            expected_fields = 5 + bool(with_seconds) + bool(with_years)
            fields = text.split(None, expected_fields)
            len_fields = len(fields)
            comment = fields.pop() if len_fields > expected_fields else ""

            if len_fields < expected_fields:
                raise MissingFieldsError(
                    "need %d fields, found %d" % (expected_fields, len_fields)
                )

            if not with_seconds:
                fields.insert(0, "*")

            if not with_years:
                fields.append("*")

        # Nothing to do if it's already in an Epoch instance or None.
        if isinstance(epoch, (Epoch, None)):
            pass

        # Unix timestamp
        elif isinstance(epoch, (int, float)):
            moment = time.localtime(epoch)
            year, month, day = moment[:3]
            epoch = Epoch(year, month, day, int(epoch))

        # (Year, Month, Day); calendar epoch only.
        elif len(epoch) == 3:
            epoch = Epoch(epoch[0], epoch[1], epoch[2], None)

        # (Year, Month, Day, Hour, Minute); calendar and clock epoch.
        elif len(epoch) >= 5:
            if len(epoch) < 9:
                epoch = list(epoch) + [0, 0, 0, -1][-(9 - len(epoch)):]

            year, month, day = epoch[:3]
            timestamp = time.mktime(when)
            epoch = Epoch(year, month, day, timestamp)

        else:
            raise Error("%r is not a supported epoch type" % (epoch, ))

        try:
            self._constraints = generate_constraint_sets(fields, epoch)
        except Error as e:
            raise Error("%s: %s" % (text.strip(), e))

        self._epoch = epoch
        self._text = text
        self._with_seconds = with_seconds
        self._with_years = with_years

        self._comment = comment.strip()
        self._expression = " ".join(text.replace(self.comment, "").split())

    def check_trigger(self, when):
        return constraints_met(
            when, self._epoch, self._with_seconds, *self._constraints)

    def __eq__(self, other):
        """
        Two CronExpression instances are considered equivalent if they have the
        same constraints. It is possible to construct two expressions that are
        not considered equal that trigger at the same time.
        """
        # TODO: The epoch doesn't necessarily apply to every field, so this
        # should be modified to only compare certain parts of the epoch based
        # on the fields that have monotonic expressions.
        try:
            if self._constraints != other._constraints:
                return False

            _, monotonic, _ = self._constraints
            if not any(monotonic):
                return True

            return self._epoch == other._epoch

        except AttributeError:
            return False

    def __repr__(self):
        template = self.__class__.__name__ + ("("
            "%(_text)r,"
            " epoch=%(_epoch)r,"
            " with_seconds=%(_with_seconds)r,"
            " with_years=%(_with_years)r"
        ")")
        return template % self.__dict__

    def __str__(self):
        return repr(self)

    @property
    def comment(self):
        return self._comment

    @property
    def expression(self):
        return self._expression

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        _text = self._text
        try:
            self.__init__(
                text=value,
                epoch=self._epoch,
                with_seconds=self._with_seconds,
                with_years=self._with_years,
            )
        except:
            self._text = _text
            raise


def atomize(field, contents):
    """
    Split a cron expression field into atomic parts that can be processed by
    "parse_atom".

    Arguments:
    - field (str): Cron expression field name.
    - contents (str): Contents of the field.

    Returns: A frozenset of atoms that can be passed to "parse_atom".
    """
    if field == FIELD_DOTW:
        replacer = lambda match: str(DAY_MAP[match.group().upper()])
        atoms = list()
        for atom in DAY_REGEX.sub(replacer, contents).split(","):
            atoms.append("0" if atom in ("7", "L") else atom)

    elif field == FIELD_MONTHS:
        replacer = lambda match: str(MONTH_MAP[match.group().upper()])
        atoms = MONTH_REGEX.sub(replacer, contents).split(",")

    else:
        atoms = contents.split(",")

    if len(atoms) > 1 and ("*" in atoms or "?" in atoms):
        raise InvalidUsage(field, "'*' / '?' must be the only text in a field")

    if "" in atoms:
        raise FieldSyntaxError(field, "missing text after comma")

    return frozenset(atoms)


def parse_atom(field, atom, epoch):
    """
    Convert a textual atoms to numeric values and day annotations.

    Arguments:
    - field (str): Cron expression field name.
    - atom (str): Expression atom.
    - epoch: Epoch representing the date and / or time from which monotonic
      constraints begin counting.

    Returns: A tuple containing (type of resulting expression, associated
    values).
    """
    if atom == "?":
        if field not in (FIELD_DAYS, FIELD_DOTW):
            raise InvalidUsage(field,
                "'?' can only appear in the days or days of the week fields"
            )
        atom = "*"

    if field == FIELD_DOTW:
        if atom.startswith("%"):
            raise InvalidUsage(field,
                "monotonic constraints cannot be used in the days of the week"
                " field"
            )

        if atom == "*":
            return (CONSTRAINT_ANNOTATION, set())

        days = set(as_annotation(field, str(n)) for n in expand(field, atom))
        if len(days) == 7:
            raise InvalidField(field,
                "\"%s\" includes every day of the week; an asterisk should be"
                " used instead"
            )

        return (CONSTRAINT_ANNOTATION, days)

    if ANNOTATABLE_FIELD_REGEX.match(atom):
        return (CONSTRAINT_ANNOTATION, set([as_annotation(field, atom)]))

    if not atom.startswith("%"):
        return (CONSTRAINT_FIXED, expand(field, atom))

    if (not epoch or None in epoch[:3]) and field in \
      (FIELD_YEARS, FIELD_MONTHS, FIELD_DAYS):
        raise FieldSyntaxError(field,
            "epoch must include a date to use monotonic constraints in the"
            " year, month or day field fields"
        )

    if (not epoch or epoch.timestamp is None) and field in \
      (FIELD_HOURS, FIELD_MINUTES, FIELD_SECONDS):
        raise FieldSyntaxError(field,
            "epoch must include a timestamp to use monotonic constraints in"
            " the hour, minute or second fields"
        )

    try:
        period = int(atom[1:])
    except ValueError:
        raise FieldSyntaxError(field, "missing integer after %%")
    else:
        if period < 2:
            raise OutOfBounds(field, "period must be greater than 1")

    # Convert monotonic constraints to fixed constraints where possible.
    if field == FIELD_YEARS:
        _, year_max = FIELD_RANGES[field]
        series = range(epoch.year, year_max, period)

    elif field == FIELD_MONTHS and not (12 % period):
        shift = epoch.month - 1
        count = 12 // period
        series = ((n * period + shift) % 12 + 1 for n in range(count))

    elif field == FIELD_SECONDS and not (60 % period):
        shift = epoch.timestamp or 0
        count = 60 // period
        series = ((n * period + shift) % 60 for n in range(count))

    else:
        return (CONSTRAINT_MONOTONIC, period)

    return (CONSTRAINT_FIXED, frozenset(series))


def as_annotation(field, expression):
    """
    Convert an textual representation of an annotation into an annotation
    tuple. This function expects the expression inputs to be well-formed; the
    caller should validate "expression" by ensuring that it matches
    "ANNOTATABLE_FIELD_REGEX".

    Arguments:
    - field: Field name.
    - expression: Expression to translate to an annotation.

    Returns: Annotation representing the expression.
    """
    if "#" in expression:
        day_of_the_week, value = map(int, expression.split("#", 1))

        if field != FIELD_DOTW:
            raise InvalidUsage(field,
                "Nth occurrence of a day of the week (%s) is only valid in the"
                " days of the week field" % (expression, )
            )

        if value < 1 or value > 5:
            raise OutOfBounds(field,
                "the week number must be greater than or equal to 1 and less"
                " than or equal to 5 (found %d in %s)" % (value, expression)
            )

        OutOfBounds.check(field, day_of_the_week, expression)
        return (ANNOTATION_XHX, day_of_the_week, value)

    if expression == "L":
        if field == FIELD_DOTW:
            raise Error(
                "L in the days-of-the-week should never reach this function"
                " because it should already be converted to a 6 by the caller"
            )

        if field == FIELD_DAYS:
            return (ANNOTATION_L_LX, 0)

        raise InvalidUsage(field,
            "'L' is only applicable to the days (last day of the month) and"
            " days of the week (last day of the week; always Saturday) fields"
        )

    if expression.startswith("L-"):
        distance = int(expression.split("-")[1])

        if distance > 30:
            raise OutOfBounds(field,
                "the longest months have 31 days, so %d days before the end of"
                " the month is invalid" % (distance, )
            )

        if field != FIELD_DAYS:
            raise InvalidUsage(field,
                "days before the end of the month (%r) is only applicable"
                " to the days field" % (expression, )
            )

        return (ANNOTATION_L_LX, distance)

    if expression.endswith("L"):
        day_of_the_week = int(expression[:-1])
        OutOfBounds.check(FIELD_DOTW, day_of_the_week, expression)

        if field != FIELD_DOTW:
            for day_name, value in DAY_MAP.items():
                if day_of_the_week == value:
                    break

            raise InvalidUsage(field,
                "last occurrence of %s. (%s) is only applicable to the days of"
                " the week field" % (expression, day_name)
            )

        return (ANNOTATION_XL, day_of_the_week)

    if expression.endswith("W"):
        if field != FIELD_DAYS:
            raise InvalidUsage(field,
                "the weekday nearest the day (%r) is only applicable to the"
                " days of the month field" % (expression, )
            )
        day = int(expression[:-1])
        OutOfBounds.check(field, day, expression)
        return (ANNOTATION_XW, day)

    dotw = int(expression)
    OutOfBounds.check(field, dotw)
    return (ANNOTATION_DOTW, dotw)


def check_monotonic(value, series, numerator=0):
    """
    Check to see if a value is a multiple of any numbers in the series. The
    value is divided by the numerator when the numerator is a non-zero value.

    Arguments:
    - value: Number.
    - series: Set of numbers representing monotonic periods.
    - numerator: When non-zero, the value is divided by this number before
      checking for membership in the series.

    Returns: A boolean True or False indicating membership.
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
    Return a set of annotations that apply to the given date. This function
    does not validate the date.

    Arguments:
    - year (int): Year of the date.
    - month (int): Month of the date.
    - day (int): Day of the month.

    Returns: A frozenset containing applicable annotations.
    """
    if month in (1, 3, 5, 7, 8, 10, 12):
        last_day_of_month = 31
    elif month in (4, 6, 9, 11):
        last_day_of_month = 30
    elif month == 2:
        last_day_of_month = 28 + (
            not (year % 4) and bool(year % 100 or not (year % 400))
        )

    y = (year - 1) if month < 3 else year
    dow = 23 * month // 9 + day + 4 + year + y // 4 - y // 100 + y // 400

    if month >= 3:
        dow -= 2
    dow %= 7

    annotations = [
        (ANNOTATION_L_LX, last_day_of_month - day),    # Days until end of month.
        (ANNOTATION_XHX, dow, (day - 1) // 7 + 1),     # Nth occurrence of DOTW.
        (ANNOTATION_DOTW, dow),                        # Day of the week.
    ]

    # Last occurrence of a particular day of the week.
    if (last_day_of_month - day) < 7:
        annotations.append((ANNOTATION_XL, dow))

    # Nearest week day for a given day of the month.
    if 1 <= dow <= 5:
        annotations.append((ANNOTATION_XW, day))

        if dow == 1:
            # Sunday -> Monday
            if day > 1:
                annotations.append((ANNOTATION_XW, day - 1))
            # Saturday --(+2d)-> Monday because Friday is in a different month
            if day == 3:
                annotations.append((ANNOTATION_XW, 1))
        elif dow == 5:
            # Friday <- Saturday
            if day < last_day_of_month:
                annotations.append((ANNOTATION_XW, day + 1))
            # Friday <-(-2d)-- Sunday because Monday is in a different month
            if (day + 3) > last_day_of_month:
                annotations.append((ANNOTATION_XW, day + 2))

    return frozenset(annotations)


def expand(field, expression):
    """
    Convert an expression for a fixed constraint into a series of numbers.

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

    Returns: A frozenset containing all values enumerated by the expression.
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
    OutOfBounds.check(field, (first, last), expression)

    if first < last:
        return frozenset(range(first, last + 1, step))

    elements = list()
    elements.extend(range(first, fmax + 1))
    elements.extend(range(fmin, last + 1))
    return frozenset(elements[::step])


def simplify_monotonic_series(series):
    """
    Remove redundant numbers from a set of monotonic periods. For example, in
    the set {5, 17, 25, 45}, the numbers 25 and 45 are redundant because they
    are both multiples of 5, so this function would return {5, 17}.
    """
    factors = list()

    for value in sorted(series):
        if not factors:
            factors.append(value)
            continue

        for factor in factors:
            if not (value % factor):
                break
        else:
            factors.append(value)

    return frozenset(factors)


def generate_constraint_sets(parts, epoch):
    """
    Convert an iterable containing cron expression fields into machine-friendly
    data structures.

    Arguments:
    - parts (iterable): Values of cron expression fields. This would generally
      be something along the lines of `text.split()`.
    - epoch: Epoch representing the date and / or time from which monotonic
      constraints begin counting.

    Returns: A tuple with 3 elements representing different constraints. The
    first element contains a set of annotations for days that match the
    constraints, the second contains one set for each field representing the
    monotonic constraints, and the third element contains one set for each
    field representing fixed constraints.
    """
    annotations = set()
    fixed = list()
    monotonic = list()

    for field, part in zip(FIELDS, parts):
        field_fixed = set()
        field_monotonic = set()

        for atom in atomize(field, part):
            mode, value = parse_atom(field, atom, epoch)
            if mode == CONSTRAINT_ANNOTATION:
                annotations.update(value)
            elif mode == CONSTRAINT_MONOTONIC:
                field_monotonic.add(value)
            elif mode == CONSTRAINT_FIXED:
                field_fixed.update(value)

        # Any field with a set of fixed constraints that include all possible
        # values are replaced with ASTERISK references.
        begin, end = FIELD_RANGES[field]
        if len(field_fixed) == (end - begin + 1):
            field_fixed = ASTERISK

        if field_fixed is ASTERISK:
            # Delete redundant constraints.
            field_monotonic = frozenset()
        elif field_monotonic:
            field_monotonic = simplify_monotonic_series(field_monotonic)

        monotonic.append(frozenset(field_monotonic))
        fixed.append(frozenset(field_fixed))

    return frozenset(annotations), Fields(*monotonic), Fields(*fixed)


def constraints_met(when, epoch, with_seconds, annotations, monotonic, fixed):
    if when is None:
        when = int(time.time())
    elif isinstance(when, float):
        when = int(when)

    if isinstance(when, int):
        timestamp = when
        year, month, day, hour, minute, second, _, _, _ = time.localtime(when)
    elif len(when) > 9:
        raise Error("time tuple has too many fields; expected 9 at most")
    elif len(when) < (6 if with_seconds else 5):
        insert = ", second and minute" if with_seconds else " and minute"
        raise Error(
            "time tuple has too few fields; at the very least, the year,"
            " month, day, hour%s must be specified" % insert
        )
    else:
        if len(when) < 9:
            when = list(when) + [0, 0, 0, -1][-(9 - len(when)):]
        timestamp = time.mktime(tuple(when))
        year, month, day, hour, minute, second, _, _, _ = when

    dS = timestamp - epoch.timestamp
    dY = year - epoch.year
    dM = dY * 12 + month - epoch.month

    if not (second in fixed.seconds or check_monotonic(dS, monotonic.seconds)):
        return False

    if not (minute in fixed.minutes or
      check_monotonic(dS, monotonic.minutes, 60)):
        return False

    if not (hour in fixed.hours or check_monotonic(dS, monotonic.hours, 3600)):
        return False

    if not (month in fixed.months or check_monotonic(dM, monotonic.months)):
        return False

    if not (year in fixed.years or check_monotonic(dY, monotonic.years)):
        return False

    # The day and day of the week fields behave differently from the others; if
    # an asterisk is used in either field, that particular field is ignored. If
    # neither field is an asterisk, the trigger fires when EITHER field
    # matches.
    if ((fixed.days is not ASTERISK and day in fixed.days) or
      check_monotonic(dS, monotonic.days, 86400)):
        return True
    elif annotations:
        return bool(annotate(year, month, day).intersection(annotations))
    else:
        return True
