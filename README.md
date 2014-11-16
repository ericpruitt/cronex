CronExpression
==============

This module provides an easy to use interface for cron-like task scheduling.
The cron expression evaluation implemented by this library is 100% Vixie Cron
compatible and also supports [Java Quartz's][JQUARTZ] non-standard "L", "W" and
"#" characters.

One other useful feature this library provides is the ability to set triggers
at arbitrary intervals such as every 9 hours, every 11 minutes, etc., without
the issues caused by using asterisk-slash notation; using `*/9` in the hours
field of most cron implementations would result in a trigger firing at 9:XX AM
at 6:XX PM each day, but with CronExpresssions, the trigger would fire at 9:XX
AM, 6:XX PM then, on the following day 3:XX AM, 12:XX PM, 9:XX PM and so.

  [JQUARTZ]: http://www.quartz-scheduler.org/documentation/quartz-1.x/tutorials/crontrigger "Quartz Scheduler: CronTrigger Tutorial"

Examples
--------

### Standard Cron Fields ###

This example shows basic instantiation of a CronExpression and how to check to
see if a trigger should fire at a given time. The time tuples consist of the
year, month, date, hour and minute in that order.

    >>> job = CronExpression("0 0 * * 1-5/2 find /var/log -delete")
    >>> job.check_trigger((2010, 11, 17, 0, 0))
    True
    >>> job.check_trigger((2012, 12, 21, 0 , 0))
    False

### Periodic Trigger ###

This trigger is a reminder to feed the kitten every 9 hours starting from May
1st, 2010 at 7 AM, GMT -6:00.

    >>> job = CronExpression("0 %9 * * * Feed kitten", (2010, 5, 1, 7, 0, -6))
    >>> job.comment
    "Feed kitten"
    >>> job.check_trigger((2010, 5, 1, 7, 0), utc_offset=-6)
    True
    >>> job.check_trigger((2010, 5, 1, 16, 0), utc_offset=-6)
    True
    >>> job.check_trigger((2010, 5, 2, 1, 0), utc_offset=-6)
    True

### Simple cron scheduler in less than ten lines ###

With CronExpressions, a very basic task scheduler can be created with only a
handful of lines.

    import time
    import os
    import cronex

    while True:
        for line in open("crontab"):
            job = cronex.CronExpression(line.strip())

            if job.check_trigger(time.gmtime(time.time())[:5]):
                os.system("(" + job.comment ") & disown")

        time.sleep(60)

Expression Syntax
-----------------

Readers that are already familiar with cron should skip down to the section
titled _Repeaters_. Aside from the repeaters, the only other notable difference
in this implementation of cron expression evaluation from Vixie Cron's is that
ranges wrap around: 22-2 in the hours field is the same as `22,23,0,1,2`.
Everything else is standard `man 5 crontab`.

Each cron trigger is specified with a combination of five white-space separated
fields that dictate when the event should occur. In order the fields specify
trigger times for minutes past the hour, hour of the day, day of the month,
month, and day of the week.

    .--------------- minute (0 - 59)
    |   .------------ hour (0 - 23)
    |   |   .--------- day of month (1 - 31)
    |   |   |   .------ month (1 - 12) or Jan, Feb ... Dec
    |   |   |   |  .---- day of week (0 - 6) or Sun(0 or 7), Mon(1) ... Sat(6)
    V   V   V   V  V
    *   *   *   *  *  command to be executed / trigger comment

There are four ways of specifying valid values for each field, all of which can
be combined with each other using commas. There are ranges, wild-cards, steps,
and repeaters. Repeaters are a non-standard addition to cron expressions that
allow specification of events with arbitrary periods.

If the hour, minute, and month of a given time period are valid values as
specified in the trigger and _either_ the day of the month _or_ the day of the
week is a valid value, the trigger fires.

### Ranges and Wild-cards ###

Ranges specify a starting and ending time period. It includes all values from
the starting value to and including the ending value.

Wild-cards, indicated with a "*", in a field represents all valid values. It is
_almost_ the same as specifying the range 0-59 in the minutes field, 0-23 in
the hours, 1-31 in days, 1-12 in months and 0-6 for weekdays.

The following cron expression is triggered every day at noon from June through
September:

    0 12 * 6-9 * * remind "Walk the ducks"

If the day of the week field is a wild card, but the day of the month is an
explicit range, the day of the week will be ignored and the trigger will only
be activated on the specified days of the month. If the day of the month is a
wild card, the same principal applies.

This expression is triggered every week day at 4:00 PM: `0 16 * * 1-5`

This one is triggered the first nine days of the month: `0 16 1-9 * *`

This one is triggered every day for the first week, but only on Saturdays
thereafter: `0 16 1-7 * 6`

### Steps ###

Steps are specified with a "/" and number following a range or wild-card. When
iterating through a range with a step, the specified number of values will be
skipped each time. `1-10/2` is the functional equivalent to `1,3,5,7,9`.

The following cron expression is triggered on the first day of every quarter
(Jan., Apr., ... Oct.) at midnight:

    0 0 1 */2 * * delete log.txt

### Repeaters ###

Repeaters cause an event to trigger after arbitrary periods of time from a
given moment which will be hitherto referred to as the epoch. By default, the
epoch is January 1st, 1970 at 0:00. Triggers in different fields operate
independently of each other: `%10 %10 * * *` would trigger at 00:00, 00:10, ...
00:50, 10:00, 10:10, etc...

The following cron expression is triggered at noon on the 10th every 5 months:

    0 12 10 %5 * Something amazing happens at noon...

### Special Symbols ###

There are three additional special symbols: "L", "W" and "#".

When used in the day of the month field, a number followed by "L" represents
the occurrence of a day of the week represented by the value preceding "L". In
the day of the month field, "L" without a prefixed integer represents the last
day of the month. `0 0 * * 5L` represent a midnight trigger for the last Friday
of each month whereas `0 0 L 2 *` represents a midnight trigger for the last
day of every February.

"W" is only valid for the field representing days of the month, and must be
prefixed with an integer. It specifies the weekday (Monday-Friday) nearest the
given day. In the construct `0 0 7W * *`, when the 7th falls on a Saturday, the
trigger will be active on the 6th. If the 7th falls on a Sunday, the trigger
will be active on the 8th.

"#" is only valid for the field representing days of the week. The "#" has a
prefix and suffix that represent the day of the week and the Nth occurrence of
that day of the week. `0 0 * * 0#5` would trigger every 5th Sunday.

### Miscellaneous ###

All of the constructs above can be combined in individual fields using commas:
`0,30 */7,5 1,%90,L 9-4/6,5-8 4#2` is a completely valid, albeit it hideous,
expression.

In addition to the atoms above, there are several special strings that can
substitute common cron expressions. These strings _replace_, not augment the
cron fields.

    String      Equivalent
    ------      ----------
    @yearly     0 0 1 1 *
    @annually   0 0 1 1 *
    @monthly    0 0 1 * *
    @weekly     0 0 * * 0
    @daily      0 0 * * *
    @midnight   0 0 * * *
    @hourly     0 * * * *
