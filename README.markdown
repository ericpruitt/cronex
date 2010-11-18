Description
-----------

This module provides an easy to use interface for cron-like task scheduling.

Example
-------
Simple scheduler in less than ten lines


    import time
    import os
    import cronex

    while True:
        for line in open("crontab"):
            job = cronex.CronExpression(line.strip())

            if job.check_trigger(time.gmtime(time.time())[:5]):
                os.system(job.comment)

        time.sleep(60)
