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

Wild-cards, indicated with a "\*", in a field represents all valid
values. It is the same as 0-59 for minutes, 0-23 for hours, 1-31 for
days, 1-12 for months and 0-6 for weekdays.

### Steps ###

Steps are specified with a "/" and number following a range or
wild-card. When iterating through a range with a step, the specified
number of values will be skipped each time. "1-10/2" is the functional
equivalent to "1,3,5,7,9".

### Periodic ###

In standard cron format, an approximation to trigger an event every 10
days might look like this: "0 0 \*/10 \* \*". This works fine for January:
The trigger is active on January 1st, 11th, and 31st; but in February,
the trigger will be active on February 1st, far ahead of schedule. One
"solution" would be to instead use "0 0 10,20,30 \* \*", but this still
does not produce an event consistently every 10 days. This is the
problem that periodicity addresses. Periodicity is represented as a "%"
followed by the length of each period. The length of the period can be
outside the bounds normal ranges of each field. "0 0 %45 \* \*" would be
active every 45 days. All periodicities are calculated starting from the
epoch and are independent of each other.

### L, W and # ###

There are three additional special symbols: "L", "W" and "#".

When used in the day of the month field, a number followed by "L"
represents the occurrence of a day of the week represented by the value
preceding "L". In the day of the month field, "L" without a prefixed
integer represents the last day of the month. "0 0 \* \* 5L" represent a
midnight trigger for the last Friday of each month whereas "0 0 L 2 \*"
represents a midnight trigger for the last day of every February.

"W" is only valid for the field representing days of the month, and must
be prefixed with an integer. It specifies the weekday (Monday-Friday)
nearest the given day. In the construct "0 0 7W \* \*", when the 7th falls
on a Saturday, the trigger will be active on the 6th. If the 7th falls
on a Sunday, the trigger will be active on the 8th.

"#" is only valid for the field representing days of the week. The "#"
has a prefix and suffix that represent the day of the week and the Nth
occurrence of that day of the week. "0 0 \* \* 0#5" would trigger every
5th Sunday.

All of the constructs above can be combined in individual fields using
commas: "0,30 \*/7,5 1,%90,L 9-4/6,5-8 4#2" is a completely valid, albeit
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
