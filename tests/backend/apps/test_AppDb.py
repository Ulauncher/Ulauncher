#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import sys
import os
import unittest
from tempfile import gettempdir

from ulauncher.backend.apps.AppDb import AppDb


class TestAppDb(unittest.TestCase):
    """AppDb"""

    def get_temp_db_name(self):
        db_file = os.path.join(gettempdir(), 'testdb')
        try:
            os.unlink(db_file)
        except:
            pass
        return db_file

    def get_app_db(self):
        try:
            return AppDb(self.get_temp_db_name()).open()
        except Exception as e:
            self.fail("Exception '%s' was raised unexpectedly: %s" % (type(e), e))

    def test_open_raises_ioerror(self):
        """It raises IOError if 'name' is a directory"""
        with self.assertRaises(IOError):
            AppDb('/tmp').open()

    def test_open_doesnt_raise(self):
        """It doesn't raise errors"""

        self.get_app_db()

    def test_commit(self):
        """It saves changes to disk"""

        file_name = os.path.join(gettempdir(), 'test_commit')
        db = AppDb(file_name).open()
        db.put({"desktop_file": "test_commit", "name": "hello"})
        db.commit()

        db = AppDb(file_name).open()
        self.assertEqual(db.find('hello')[0]['desktop_file'], 'test_commit')

    def get_db_with_data(self):
        db = self.get_app_db()
        db.put({'name': 'john', 'description': 'test', 'desktop_file': 'john.desktop', 'icon': 'icon'})
        db.put({'name': 'james', 'description': 'test', 'desktop_file': 'james.desktop', 'icon': 'icon'})
        db.put({'name': 'o.jody', 'description': 'test', 'desktop_file': 'o.jdy.desktop', 'icon': 'icon'})
        db.put({'name': 'sandy', 'description': 'test', 'desktop_file': 'sandy.desktop', 'icon': 'icon'})
        db.put({'name': 'sane', 'description': 'test', 'desktop_file': 'jane.desktop', 'icon': 'icon'})
        return db

    def test_find_max_results(self):
        """It returns no more than limit"""

        db = self.get_db_with_data()
        self.assertEqual(len(db.find('j', limit=3)), 3)
        self.assertEqual(len(db.find('j', limit=2)), 2)

    def test_find_filters_by_min_score(self):
        """It returns matches only if score > min_score"""

        db = self.get_db_with_data()
        self.assertEqual(len(db.find('jo', min_score=50)), 2)
        self.assertEqual(len(db.find('jo', min_score=92)), 0)

    def test_remove(self):
        db = self.get_app_db()
        db.put({'name': 'john', 'description': 'test', 'desktop_file': 'john.desktop', 'icon': 'icon'})
        db.put({'name': 'james', 'description': 'test', 'desktop_file': 'james.desktop', 'icon': 'icon'})
        self.assertTrue(db.records.get('james'))
        db.remove('james')
        self.assertFalse(db.records.get('james'))
