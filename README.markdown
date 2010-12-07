CronExpression
--------------

This module provides an easy to use interface for cron-like task scheduling.

Examples
========

### Standard Cron Fields: ###

    >>> job = CronExpression("0 0 * * 1-5/2 find /var/log -delete")
    >>> job.check_trigger((2010, 11, 17, 0, 0))
    True
    >>> job.check_trigger((2012, 12, 21, 0 , 0))
    False

### Periodic Trigger: ###

    >>> job = CronExpression("0 %9 * * * Feed 'it'", (2010, 5, 1, 7, 0, -6))
    >>> job.comment
    "Feed 'it'"
    >>> job.check_trigger((2010, 5, 1, 7, 0), utc_offset=-6)
    True
    >>> job.check_trigger((2010, 5, 1, 16, 0), utc_offset=-6)
    True
    >>> job.check_trigger((2010, 5, 2, 1, 0), utc_offset=-6)
    True

### Simple cron scheduler in less than ten lines:  ###

    import time
    import os
    import cronex

    while True:
        for line in open("crontab"):
            job = cronex.CronExpression(line.strip())

            if job.check_trigger(time.gmtime(time.time())[:5]):
                os.system(job.comment)

        time.sleep(60)
