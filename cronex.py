#!/usr/bin/env python
"""
This module provides a class for cron-like scheduling systems, and
exposes the function used to convert static cron expressions to Python
sets.

Example: Simple scheduler in less than ten lines

    import cronex
    import os
    import time

    while True:
        for line in open("crontab"):
            job = cronex.CronExpression(line.strip())

            if job.check_trigger(time.gmtime(time.time())[:5]):
                os.system(job.comment)

        time.sleep(60)
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
L_FIELDS = (DAYS_OF_WEEK, DAYS_OF_MONTH)
FIELD_RANGES = (MINUTES, HOURS, DAYS_OF_MONTH, MONTHS, DAYS_OF_WEEK)
MONTH_NAMES = zip(('jan', 'feb', 'mar', 'apr', 'may', 'jun',
                   'jul', 'aug', 'sep', 'oct', 'nov', 'dec'), xrange(1, 13))
DEFAULT_EPOCH = (1970, 1, 1, 0, 0, 0)
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
    def __init__(self, line, epoch=DEFAULT_EPOCH, epoch_utc_offset=0):
        """
        Instantiates a CronExpression object with an optionally defined epoch.
        """
        self.rawentry = line.strip()

        for key, value in SUBSTITUTIONS.items():
            if line.startswith(key):
                line = line.replace(key, value)
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
        self.compute_numtab()
        if len(epoch) == 5:
            y, mo, d, h, m = epoch
            self.epoch = (y, mo, d, h, m, epoch_utc_offset)
        else:
            self.epoch = epoch

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

        for field_str, span in zip(self.string_tab, FIELD_RANGES):
            unified = set()
            for cron_atom in field_str.split(','):
                # parse_atom only handles static cases
                for special_char in ('%', '#', 'L', 'W'):
                    if special_char in cron_atom:
                        break
                else:
                    unified.update(parse_atom(cron_atom, span))

            self.numerical_tab.append(unified)

        if self.string_tab[2] == "*" and self.string_tab[4] != "*":
            self.numerical_tab[2] = set()

    def check_trigger(self, date_tuple, utc_offset=0):
        """
        Returns boolean indicating whether the trigger fires at the given time
        """
        year, month, day, hour, mins = date_tuple
        givenday = datetime.date(year, month, day)
        zeroday = datetime.date(*self.epoch[:3])
        lastdom = calendar.monthrange(year, month)[-1]

        # In calendar.monthrange and datetime.date.weekday, Monday = 0
        givendow = (datetime.date.weekday(givenday) + 1) % 7
        firstdow = (givendow + 1 - day) % 7

        # Figure out how much time has passed from the epoch to the given date
        utc_diff = utc_offset - self.epoch[5]
        mod_delta_yrs = year - self.epoch[0]
        mod_delta_mon = month - self.epoch[1] + mod_delta_yrs * 12
        mod_delta_day = (givenday - zeroday).days
        mod_delta_hrs = hour - self.epoch[3] + mod_delta_day * 24 + utc_diff
        mod_delta_min = mins - self.epoch[4] + mod_delta_hrs * 60

        # Makes iterating through like components easier.
        quintuple = zip(
            (mins, hour, day, month, givendow),
            self.numerical_tab,
            self.string_tab,
            (mod_delta_min, mod_delta_hrs, mod_delta_day, mod_delta_mon, 0),
            FIELD_RANGES)

        for value, validnums, field_str, timediff, field_type in quintuple:
            # All valid, static values for the fields are stored in sets
            if value in validnums:
                continue

            # The following for loop implements the logic for context
            # sensitive and epoch sensitive constraints. break statements,
            # which are executed when a match is found, lead to a continue
            # in the outer loop. If there are no matches found, the given date
            # does not match expression constraints, so the function returns
            # False as seen at the end of this for...else... construct.
            for cron_atom in field_str.split(','):
                if cron_atom[0] == '%':
                    if not(timediff % int(cron_atom[1:])):
                        break

                elif field_type == DAYS_OF_WEEK and '#' in cron_atom:
                    D, N = int(cron_atom[0]), int(cron_atom[2])
                    # Computes Nth occurence of D day of the week
                    if (((D - firstdow) % 7) + 1 + 7 * (N - 1)) == day:
                        break

                elif field_type == DAYS_OF_MONTH and cron_atom[-1] == 'W':
                    target = min(int(cron_atom[:-1]), lastdom)
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

                elif field_type in L_FIELDS and cron_atom.endswith('L'):
                    # In dom field, translates to last d.o.m.
                    target = lastdom

                    if field_type == DAYS_OF_WEEK:
                        # Calculates the last occurence of given day of week
                        desired_dow = int(cron_atom[:-1])
                        target = (((desired_dow - firstdow) % 7) + 29)
                        target -= 7 if target > lastdom else 0

                    if target == day:
                        break
            else:
                # See 2010.11.15 of CHANGELOG
                if field_type == DAYS_OF_MONTH and self.string_tab[4] != '*':
                    continue
                elif field_type == DAYS_OF_WEEK and self.string_tab[2] != '*':
                    # If we got here, then days of months validated.
                    return True

                # None of the expressions matched which means this field fails
                return False

        # Arriving at this point means the date landed within the constraints
        # of all fields; the associated trigger should be fired.
        return True

def parse_atom(parse, minmax):
    """
    Returns valid values for a given cron-style range of numbers.

    :minmax: Length 2 iterable containing the valid suffix and prefix bounds
    for the range. The range is inclusive on both bounds.

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
            ceilvalue = increment - (minmax[1] - top[-1] - 1)
            bottom = set(xrange(ceilvalue - minmax[0], suffix + 1, increment))
            bottom.update(top)
            return bottom
