#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import site
import unittest
import time
import sys

MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR

# Add the parent directory relative to the test case because we assume the
# test will be in a subdirectory relative to the main code base.
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.realpath(__file__)), os.pardir))

import cronex

class test_testedmodule(unittest.TestCase):
    def test_substitution(self):
        testcases = [("@yearly", "0 0 1 1 *"),
            ("@anually", "0 0 1 1 *"),
            ("@monthly", "0 0 1 * *"),
            ("@weekly", "0 0 * * 0"),
            ("@daily", "0 0 * * *"),
            ("@midnight", "0 0 * * *"),
            ("@hourly", "0 * * * *")]
        for a, b in testcases:
            obj = cronex.CronExpression(a)
            self.assertTrue(b in repr(obj))

    def test_compute_numtab(self):
        testex1 = cronex.CronExpression("*/7 5-10 5 * *")
        testex2 = cronex.CronExpression("*/5 23-2 5 8 *")
        self.assertNotEqual(testex1.string_tab, testex2.string_tab)
        self.assertNotEqual(testex1.numerical_tab, testex2.numerical_tab)
        testex1.string_tab = testex2.string_tab
        testex1.compute_numtab()
        self.assertEqual(testex1.string_tab, testex2.string_tab)
        self.assertEqual(testex1.numerical_tab, testex2.numerical_tab)

    def test_periodics_dom(self):
        now = int(time.time())
        then = time.gmtime(now - 491 * DAY)
        now_tuple = time.gmtime(now)
        testex = cronex.CronExpression("* * %491 * *")
        self.assertFalse(testex.check_trigger(now_tuple[:5]))
        testex.epoch = tuple(list(then[:5]) + [0])
        self.assertTrue(testex.check_trigger(now_tuple[:5]))
        self.assertTrue(testex.check_trigger(then[:5]))

    def test_periodics_hours(self):
        now = int(time.time())
        then = time.gmtime(now - 9001 * HOUR)
        now_tuple = time.gmtime(now)
        testex = cronex.CronExpression("* %9001 * * *")
        self.assertFalse(testex.check_trigger(now_tuple[:5]))
        testex.epoch = tuple(list(then[:5]) + [0])
        self.assertTrue(testex.check_trigger(now_tuple[:5]))
        self.assertTrue(testex.check_trigger(then[:5]))

    def test_periodics_minutes(self):
        now = int(time.time())
        then = time.gmtime(now - 814075 * MINUTE)
        now_tuple = time.gmtime(now)
        testex = cronex.CronExpression("%814075 * * * *")
        self.assertFalse(testex.check_trigger(now_tuple[:5]))
        testex.epoch = tuple(list(then[:5]) + [0])
        self.assertTrue(testex.check_trigger(now_tuple[:5]))
        self.assertTrue(testex.check_trigger(then[:5]))

    def test_periodics_month(self):
        now = int(time.time())
        then = time.gmtime(now - 1337 * DAY)
        now_tuple = time.gmtime(now)
        curmon = now_tuple[1]
        thnmon = then[1]
        per = 36 + curmon - thnmon
        testex = cronex.CronExpression("* * * %%%i *" % per)
        self.assertFalse(testex.check_trigger(now_tuple[:5]))
        testex.epoch = tuple(list(then[:5]) + [0])
        self.assertTrue(testex.check_trigger(now_tuple[:5]))
        self.assertTrue(testex.check_trigger(then[:5]))

    def test_parse_atom(self):
        input_expect = [
            (('5-10',(1,20)), set([5,6,7,8,9,10])),
            (('10-5',(1,12)), set([10,11,12,1,2,3,4,5])),
            (('5-10/2',(1,20)), set([5,7,9])),
            (('10-5/2',(1,12)),set([10, 12, 2, 4])),
            (('11-5/2',(1,12)),set([11, 1, 3, 5])),
            (('10-5/3',(1,11)),set([10, 2, 5])),
            (('11-5/3',(1,14)),set([11, 14, 3])),
            (('*',(1, 100)), set(xrange(1,101))),
            (('*/5',(1,100)), set(xrange(1,101,5))),
            (('666',(1,1000)), set([666]))]

        for give_the_function, want_from_function in input_expect:
            self.assertEqual(want_from_function,
                cronex.parse_atom(*give_the_function))

    def test_str_and_repr(self):
        CronExpression = cronex.CronExpression
        testex1 = cronex.CronExpression("*/15 4 1-7 * * TEST___TEST")
        testex2 = eval(repr(testex1))
        self.assertEqual(testex1.string_tab, testex2.string_tab)
        self.assertEqual(testex1.numerical_tab, testex2.numerical_tab)
        self.assertEqual(testex1.comment, testex2.comment)
        self.assertEqual(repr(testex1), str(testex1))

    def test_dom_substitution(self):
        testex1 = cronex.CronExpression(
            "* * * jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec *")
        testex2 = cronex.CronExpression("* * * 1,2,3,4,5,6,7,8,9,10,11,12 *")
        self.assertEqual(repr(testex1), repr(testex2))

    def test_dow_substitution(self):
        testex1 = cronex.CronExpression("* * * * sun,mon,tue,wed,thu,fri,sat")
        testex2 = cronex.CronExpression("* * * * 0,1,2,3,4,5,6")
        self.assertEqual(repr(testex1), repr(testex2))

    def test_dom_either_or_dow(self):
        testex = cronex.CronExpression("0 0 5 * mon")
        self.assertTrue(testex.check_trigger((2010,11,5,0,0)))
        self.assertTrue(testex.check_trigger((2010,11,1,0,0)))
        self.assertTrue(testex.check_trigger((2010,11,8,0,0)))
        self.assertTrue(testex.check_trigger((2010,11,15,0,0)))
        self.assertTrue(testex.check_trigger((2010,11,22,0,0)))
        self.assertTrue(testex.check_trigger((2010,11,29,0,0)))

        testex = cronex.CronExpression("0 0 * * wed")
        for d in xrange(1,32):
            if not(d % 7):
                self.assertTrue(testex.check_trigger((2010,7,d,0,0)))
            else:
                self.assertFalse(testex.check_trigger((2010,7,d,0,0)))

    def test_L_in_dow(self):
        testex = cronex.CronExpression("0 0 * * 6L")
        tv = [30,27,27,24,29,26,31,28,25,30,27,25]
        for v in xrange(0,12):
            self.assertTrue((testex.check_trigger((2010,v+1,tv[v],0,0))))

    def test_L_in_dom(self):
        testex = cronex.CronExpression("0 0 L * *")
        import calendar
        for y in xrange(2000, 2009):
            for v in xrange(1,13):
                self.assertTrue(testex.check_trigger((y,v,calendar.monthrange(
                    y,v)[-1],0,0)))

    def test_calendar_change_vs_hour_change(self):
        # epoch and local differ by < 48 hours but it should be reported based 
        # on calendar days, not 24 hour days
        epoch = (2010, 11, 16, 23, 59)    
        local_time = (2010, 11, 18, 0, 0)
        testex = cronex.CronExpression("0 0 %2 * *",epoch, -6)
        self.assertTrue(testex.check_trigger(local_time, -6))

def suite():
    s = unittest.makeSuite(test_testedmodule)
    return unittest.TestSuite([s])

if __name__ == "__main__":
    unittest.main()
