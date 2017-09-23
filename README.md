Cronex (Cron Expressions)
=========================

This module provides an easy to use interface for cron-like task scheduling.
The syntax supported by this library is Vixie Cron compatible, and cronex also
has limited compatibility with the [Quartz job scheduling library][quartz].
Other notable features include:

- Support for specifying expressions with conditions for seconds and / or
  years.
- The ability to set triggers at arbitrary intervals such as every 9 hours,
  every 11 minutes, etc., without the issues associated with traditional range
  expressions. For example: using "*/9" in the hours field of most cron
  implementations would result in a trigger firing at 9:XX AM and 6:XX PM each
  day. With Cronex, "%9" can be used to make a trigger that would fire at 9:XX
  AM, 6:XX PM then, on the following day, 3:XX AM, 12:XX PM, 9:XX PM and so.

  [quartz]: http://www.quartz-scheduler.org/ "Quartz Enterprise Job Scheduler"

Examples
--------

### Standard Cron Fields ###

This example shows basic instantiation of a CronExpression and how to check to
see if a trigger should fire at a given time. The time tuples consist of the
year, month, date, hour and minute in that order.

    >>> task = CronExpression("0 0 * * 1-5/2 find /var/log -delete")
    >>> task.check_trigger((2010, 11, 17, 0, 0))
    True
    >>> task.check_trigger((2012, 12, 21, 0 , 0))
    False

### Monotonic Expression ###

    >>> task = CronExpression("0 %9 * * * Feed kitten", (2010, 5, 1, 7, 0, -6))
    >>> task.comment
    "Feed kitten"
    >>> task.check_trigger((2010, 5, 1, 7, 0))
    True
    >>> task.check_trigger((2010, 5, 1, 16, 0))
    True
    >>> task.check_trigger((2010, 5, 2, 1, 0))
    True

### Basic Cron Job System ###

    #!/usr/bin/env python
    import os
    import time

    import cronex

    # Load tasks from file.
    tasks = list()
    with open("crontab") as crontab:
        for line in crontab:
            tasks.append(cronex.CronExpression(line))

    # Every minute, check and run triggered tasks.
    while True:
        now = time.time()
        for task in tasks:
            if task.check_trigger(now):
                os.system("( " + task.comment + " ) >/dev/null 2>&1 &")

        time.sleep(60 - time.time() % 60)

Syntax
------

### Basics ###

Each cron trigger is specified with a combination of at least five white-space
separated fields that dictate when the event should occur. In order, the fields
specify trigger times for the minute, hour, day of the month, month and the day
of the week.

    .--------------- Minute (0 - 59)
    |   .------------ Hour (0 - 23)
    |   |   .--------- Day of the month (1 - 31)
    |   |   |   .------ Month (1 - 12) or Jan, Feb ... Dec
    |   |   |   |   .---- Day of the week (0 (Sun.; also 7) - 6 (Sat.))
    V   V   V   V   V
    *   *   *   *   *

If the hour, minute, and month of a given time period are valid values as
specified in the trigger and _either_ the day of the month _or_ the day of the
week is a valid value, the trigger fires.

<!-- <TBD> -->

### Ranges and Wild-cards ###

Ranges specify a starting and ending time period. It includes all values from
the starting value to and including the ending value.

Wild-cards ("*") in a field represents all valid values.

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

<!-- </TBD> -->

### Monotonic Triggers ###

In typical cron implementations, setting the hour field to "*/9" would mean
cause it to match the hours 00:XX, 09:XX and 18:XX. The following day, pattern
would begin again starting from 00:XX making it impossible to easily define an
event that occurs every 9 hours. Monotonic triggers are Cronex's solution to
this problem; "%" in any field except the day of the week can be used to denote
expressions that should happen every N-intervals.

Monotonic expressions in the year, month and day field use calendar values. For
example, using "%15" in the day field with an epoch set to January 1st, 2017
would cause the days to match on January 1st, 16th and the 31st regardless of
the time zone.

Monotonic expressions in the hours field will not work correctly if the local
time zone's offset from UTC shifts by anything other than whole hour
increments; going from -07:00 to -08:00, 09:00 to -04:00 and -00:45 to +00:45
is fine, but going from -10:30 to -11:00, -07:15 to -08:45 and +00:15 to +00:45
will result in triggers firing at bizarre times. At the time of this writing,
only two time zones are known to be impacted by this: Lord Howe Island uses
UTC+10:30 for standard time and UTC+11:00 for daylight savings, and Venezuela
changed its local time from UTC-04:30 to UTC-04:00 on May 1st, 2016. Since the
change in Venezuela's offset was a one-off event, monotonic expressions can
safely be used with its time zone as long as the epoch is set to a moment after
the change.

### Quartz Compatibility ###

Cronex has some syntactical compatibility with Quartz. These descriptions have
been adapted from the [library's documentation][quartz-1.x-tutorial]:

- **L**: Short for "last," it has a different meaning in each of the two fields
  in which it is allowed. For example, the value "L" in the day-of-month field
  means "the last day of the month" - day 31 for January, day 28 for February
  on non-leap years. If used in the day-of-week field by itself, it simply
  means "6" or "SAT". If it is used in the day-of-week field after another
  value, it means "the last occurrence of a day of the week in the month;" for
  example, "5L" means "the last Friday of the month."

- **W**: Short for "weekday," it is used to specify the weekday (Monday-Friday)
  nearest the given day. As an example, specifying "15W" as the value for the
  day-of-month field, the meaning is "the nearest weekday to the 15th of the
  month." So if the 15th is a Saturday, the trigger will fire on Friday the
  14th. If the 15th is a Sunday, the trigger will fire on Monday the 16th. If
  the 15th is a Tuesday, then it will fire on Tuesday the 15th. However,
  specifying "1W" as the value for day-of-month, and the 1st is a Saturday, the
  trigger will fire on Monday the 3rd, as it will not "jump" over the boundary
  of a month's days. The "W" character can only be specified when the
  day-of-month is a single day, not a range or list of days.

- **LW**: The "L" and "W" characters can also be combined in the day-of-month
  field to yield "LW", which translates to "last weekday of the month".

- **#**: Used to specify the Nth occurrence of a day of the week in a month.
  For example, "6#3" in the day-of-week field means "the third Saturday of the
  month;" day 6 is Saturday, and "#3" represents the 3rd one in the month.
  Other examples: "2#1" refers to the first Tuesday of the month and "4#5" the
  fifth Thursday of the month. When specifying "#5" for a day of the week that
  only occurs four times in a particular month, the trigger will not fire that
  month.

  [quartz-1.x-tutorial]: http://www.quartz-scheduler.org/documentation/quartz-1.x/tutorials/crontrigger "Quartz Scheduler: CronTrigger Tutorial"
