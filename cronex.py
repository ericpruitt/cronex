#!/usr/bin/env python
"""
DESCRIPTION
-----------
This module provides a class for cron-like scheduling systems, and
exposes the function used to convert static cron expressions to Python
sets.

An instance of the CronExpression class is instantiated with a string
and an optional iterable compose of 5 elements that represent the year,
month, day, hour and minute, respectively, to define a starting epoch
for the CronExpression. The epoch, which defaults to 1970-01-01T00:00Z,
is used for a non-standard option this module permits: defining valid
trigger times in arbitrary periods for every field including days of the
week. The instantiation string must contain five white space separated
fields. Any text following those fields will be saved under the class
variable "comment." After an instance of CronExpression is generated,
the epoch can be modified by simply changing the value of
CronExpression.epoch.

    >>> task = CronExpression("0 0 1 1 * find /var/log -delete")
    >>> task.comment
    'find /var/log -delete'


FIELD SYNTAX
------------

Cron fields must be defined in the following order: minute, hour, day of
the month, month, and day of the week. All fields permit arbitrary
listing of values, ranges, wild-cards, steps and periodicity. In the
field for days of the week, 0 represents Sunday and 6 Saturday. The
months and days of the week fields permit using three letter
abbreviations such as "dec" for December and "tue" for Tuesday in place
of numbers. All abbreviations are case insensitive.

Lone integers can be specified for each field, or multiple values can be
used by separating them with commas. In the field representing days of
the month, "5,10,25" would represent the 5th, 10th and 25th day of each
month.

### Ranges ###

Ranges are defined with a hyphen separating the initial and terminal
values. In the hour field, "6-14" would mean all from 6:00am to 2:00pm.
All ranges are inclusive of both values. If the first value is greater
than the second value, this will be interpreted to mean the range should
wrap-around. If "10-2" were specified in the months field, it would be
interpreted to mean October, November, December, January and February.

### Wild-cards ###

Wild-cards, indicated with a "*", in a field represents all valid
values. It is the same as 0-59 for minutes, 0-23 for hours, 1-31 for
days, 1-12 for months and 0-6 for weekdays.

### Steps ###

Steps are specified with a "/" and number following a range or
wild-card. When iterating through a range with a step, the specified
number of values will be skipped each time. "1-10/2" is the functional
equivalent to "1,3,5,7,9".

### Periodic ###

In standard cron format, an approximation to trigger an event every 10
days might look like this: "0 0 */10 * *". This works fine for January:
The trigger is active on January 1st, 11th, and 31st; but in February,
the trigger will be active on February 1st, far ahead of schedule. One
"solution" would be to instead use "0 0 10,20,30 * *", but this still
does not produce an event consistently every 10 days. This is the
problem that periodicity addresses. Periodicity is represented as a "%"
followed by the length of each period. The length of the period can be
outside the bounds normal ranges of each field. "0 0 %45 * *" would be
active every 45 days. All periodicities are calculated starting from the
epoch and are independent of each other.

### L, W and # ###

There are three additional special symbols: "L", "W" and "#".

When used in the day of the month field, a number followed by "L"
represents the occurrence of a day of the week represented by the value
preceding "L". In the day of the month field, "L" without a prefixed
integer represents the last day of the month. "0 0 * * 5L" represent a
midnight trigger for the last Friday of each month whereas "0 0 L 2 *"
represents a midnight trigger for the last day of every February.

"W" is only valid for the field representing days of the month, and must
be prefixed with an integer. It specifies the weekday (Monday-Friday)
nearest the given day. In the construct "0 0 7W * *", when the 7th falls
on a Saturday, the trigger will be active on the 6th. If the 7th falls
on a Sunday, the trigger will be active on the 8th.

"#" is only valid for the field representing days of the week. The "#"
has a prefix and suffix that represent the day of the week and the Nth
occurrence of that day of the week. "0 0 * * 0#5" would trigger every
5th Sunday.

All of the constructs above can be combined in individual fields using
commas: "0,30 */7,5 1,%90,L 9-4/6,5-8 4#2" is a completely valid, albeit
it hideous, expression.

SPECIAL STRINGS
----------------

There are several special strings that can substitute common cron
expressions.

    String      Equivalent
    ------      ----------
    @yearly     0 0 1 1 *
    @anually    0 0 1 1 *
    @monthly    0 0 1 * *
    @weekly     0 0 * * 0
    @daily      0 0 * * *
    @midnight   0 0 * * *
    @hourly     0 * * * *

These strings _replace_, not augment the cron fields.

    >>> task = CronExpression("@yearly")
    >>> repr(task)
    'CronExpression("0 0 1 1 *")'


METHODS
-------

After a CronExpression is instantiated, there are two methods associated
with it: compute_numtab and check_trigger. compute_numtab only needs to
be executed if the CronExpression.string_tab, a list containing the
different fields in string form, is modified. check_trigger accepts 5
arguments that represent the date in ISO 8601 format. A Boolean is
returned representing whether or not the trigger is active at the
supplied time.


EXAMPLES
--------

    >>> task = CronExpression("0 0 1 1 * find /var/log -delete")
    >>> task.check_trigger(2010, 11, 14, 0, 0)
    False
    >>> task.check_trigger(2010, 1, 1, 0, 0)
    True

    >>> epoch_fun = CronExpression("0 0 %45 * *")
    >>> epoch_fun.check_trigger(2010, 2, 15, 0, 0)
    False
    >>> epoch_fun.check_trigger(1970, 2, 15, 0, 0)
    True
    >>> epoch_fun.epoch = (2010, 1, 1, 0, 0)
    >>> epoch_fun.check_trigger(2010, 2, 15, 0, 0)
    True
"""

import datetime
import calendar

__all__ = ["CronExpression", "parse_atom", "DEFAULT_EPOCH", "SUBSTITUTIONS"]
__license__ = "Public Domain"

DAY_NAMES = zip(('sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'), xrange(7))
MINUTES = (0, 59)
HOURS = (0, 23)
DAYS_OF_MONTH = (1, 31)
MONTHS = (1, 12)
DAYS_OF_WEEK = (0, 6)
SUPPORTS_L_CHR = (DAYS_OF_WEEK, DAYS_OF_MONTH)
FIELD_RANGES = (MINUTES, HOURS, DAYS_OF_MONTH, MONTHS, DAYS_OF_WEEK)
MONTH_NAMES = zip(('jan', 'feb', 'mar', 'apr', 'may', 'jun',
                   'jul', 'aug', 'sep', 'oct', 'nov', 'dec'), xrange(1, 13))
DEFAULT_EPOCH = (1970, 1, 1, 0, 0)
SUBSTITUTIONS = {
    "@yearly": "0 0 1 1 *",
    "@anually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *"
}

class CronExpression(object):
    def __init__(self, line, epoch=DEFAULT_EPOCH):
        """
        Instantiates a CronExpression object with an optionally defined epoch.
        """
        self.rawentry = line.strip()

        for key in SUBSTITUTIONS:
            if line.startswith(key):
                line = line.replace(key, SUBSTITUTIONS[key])
                break

        fields = line.split(None, 5)
        if len(fields) == 5:
            fields.append('')

        minutes, hours, dom, months, dow, self.comment = fields

        dow = dow.replace('7', '0').replace('?', '*')
        dom = dom.replace('?', '*')

        for monthstr, monthnum in MONTH_NAMES:
            months = months.lower().replace(monthstr, str(monthnum))

        for dowstr, downum in DAY_NAMES:
            dow = dow.lower().replace(dowstr, str(downum))

        self.string_tab = [minutes, hours, dom.upper(), months, dow.upper()]
        self.epoch = epoch
        self.compute_numtab()

    def __str__(self):
        base = self.__class__.__name__ + "(%s)"
        strformat = self.string_tab + [self.comment]
        if not self.comment:
            strformat.pop()
        arguments = '"' + ' '.join(strformat) + '"'
        if self.epoch != DEFAULT_EPOCH:
            return base % (arguments + ", epoch=" + repr(self.epoch))
        else:
            return base % arguments

    def __repr__(self):
        return str(self)

    def compute_numtab(self):
        """
        Recomputes the sets for the static ranges of the trigger time
        """
        self.numerical_tab = []
        for cron_field, span in zip(self.string_tab, FIELD_RANGES):
            unified = set()
            for cron_expression in cron_field.split(','):
                # parse_atom only handles static cases
                for special_char in ('%', '#', 'L', 'W'):
                    if special_char in cron_expression:
                        break
                else:
                    unified.update(parse_atom(cron_expression, span))

            self.numerical_tab.append(unified)

    def check_trigger(self, year, month, day, hour, mins):
        """
        Returns boolean indicating whether the trigger fires at the given time
        """
        givenday = datetime.date(year, month, day)
        zeroday = datetime.date(*self.epoch[:3])
        lastdom = calendar.monthrange(year, month)[-1]

        # In "calendar.monthrange" and datetime.date.weekday, Monday = 0
        givendow = (datetime.date.weekday(givenday) + 1) % 7
        firstdow = (givendow + 1 - day) % 7

        # Figure out how much time has passed from the epoch to the given date
        mod_delta_yrs = year - self.epoch[0]
        mod_delta_mon = month - self.epoch[1] + mod_delta_yrs * 12
        mod_delta_day = (givenday - zeroday).days
        mod_delta_hrs = hour - self.epoch[3] + mod_delta_day * 24
        mod_delta_min = mins - self.epoch[4] + mod_delta_hrs * 60

        # Makes iterating through like components easier.
        quaple = zip(
            (mins, hour, day, month, givendow),
            self.numerical_tab,
            self.string_tab,
            (mod_delta_min, mod_delta_hrs, mod_delta_day, mod_delta_mon, 0))

        for value, validnums, cron_field, timediff in quaple:
            # All valid, static values for the fields are stored in sets
            if value in validnums:
                continue

            # The following for loop implements the logic for context
            # sensitive and epoch sensitive constraints. break statements,
            # which are executed when a match is found, lead to a continue
            # in the outer loop. If there are no matches found, the given date
            # does not match expression constraints, so the function returns
            # False as seen at the end of this for...else... construct.
            for cron_expression in cron_field.split(','):
                if cron_expression[0] == '%':
                    if not(timediff % int(cron_expression[1:])):
                        break

                elif cron_field == DAYS_OF_WEEK and cron_expression[1] == '#':
                    D, N = int(cron_expression[0]), int(cron_expression[2])
                    # Computes Nth occurence of D day of the week
                    if (((D - firstdow) % 7) + 1 + 7 * (N - 1)) == day:
                        break

                elif cron_field == DAYS_OF_MONTH and cron_expression[-1] == 'W':
                    target = min(int(cron_expression[:-1]), lastdom)
                    lands_on = (firstdow + target - 1) % 7
                    if lands_on == 0:
                        # Shift from Sun. to Mon. unless Mon. is next month
                        target += 1 if target < lastdom else -2
                    elif lands_on == 6:
                        # Shift from Sat. to Fri. unless Fri. in prior month
                        target += -1 if target > 1 else 2

                    # Break if the day is correct, and target is a weekday
                    if target == day and (firstdow + target - 7) % 7 > 1:
                        break

                elif cron_field in SUPPORTS_L_CHR and cron_expression.endswith('L'):
                    # In dom field, translates to last d.o.m.
                    target = lastdom

                    if cron_field == DAYS_OF_WEEK:
                        # Calculates the last occurence of given day of week
                        desired_dow = int(cron_expression[:-1])
                        target = (((desired_dow - firstdow) % 7) + 29)
                        target -= 7 if target > lastdom else 0

                    if target == day:
                        break
            else:
                # None of the expressions matched which means this field fails
                return False

        # Arriving at this point means the date landed within the constraints
        # of all fields; the associated trigger should be fired.
        return True

def parse_atom(parse, minmax):
    """
    Returns valid values for a given cron-style range of numbers.

    :minmax: Length 2 iterable containing the valid suffix and prefix bounds for
    the range. The range is inclusive on both bounds.

    Examples:
    >>> parse_atom("1-5",(0,6))
    set([1, 2, 3, 4, 5])

    >>> parse_atom("*/6",(0,23))
    set([0, 6, 12, 18])

    >>> parse_atom("18-6/4",(0,23))
    set([18, 22, 0, 4])

    >>> parse_atom("*/9",(0,23))
    set([0, 9, 18])
    """
    parse = parse.strip()
    increment = 1
    if parse == '*':
        return set(xrange(minmax[0], minmax[1] + 1))
    elif parse.isdigit():
        # A single number still needs to be returned as a set
        return set((int(parse),))
    elif '-' in parse or '/' in parse:
        divide = parse.split('/')
        subrange = divide[0]
        if len(divide) == 2:
            # Example: 1-3/5 or */7 increment should be 5 and 7 respectively
            increment = int(divide[1])

        if '-' in subrange:
            # Example: a-b
            prefix, suffix = [int(n) for n in subrange.split('-')]
            if prefix < minmax[0] or suffix > minmax[1]:
                raise ValueError("Invalid bounds: \"%s\"" % parse)
        elif subrange == '*':
            # Include all values with the given range
            prefix, suffix = minmax
        else:
            raise ValueError("Unrecognized symbol: \"%s\"" % subrange)

        if prefix < suffix:
            # Example: 7-10
            return set(xrange(prefix, suffix + 1, increment))
        else:
            # Example: 12-4/2; (12, 12 + n, ..., 12 + m*n) U (n_0, ..., 4)
            top = xrange(prefix, minmax[1] + 1, increment)
            adjustment = increment - (minmax[1] - top[-1] - 1)
            bottom = set(xrange(adjustment - minmax[0], suffix + 1, increment))
            bottom.update(top)
            return bottom
