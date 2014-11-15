import os
import pickle
from fuzzywuzzy import process
from distutils.dir_util import mkpath


class AppDb(object):
    def __init__(self, basename):
        """
        :param str basename: path to db file
        """
        self.name = basename
        self.records = {}

    def open(self, overwrite=False):
        """Create a new data base or open existing one"""
        if os.path.exists(self.name):
            if not os.path.isfile(self.name):
                raise IOError("%s exists and is not a file" % self.name)

            with open(self.name, 'rb') as _in:  # binary mode
                self.records = pickle.load(_in)
        else:
            # make sure path exists
            mkpath(os.path.dirname(self.name))
            self.commit()

        return self

    def commit(self):
        """Write the database to a file"""
        with open(self.name, 'wb') as out:
            pickle.dump(self.records, out, pickle.HIGHEST_PROTOCOL)
            out.close()

        return self

    def remove(self, desktop_file):
        """
        :param str desktop_file:
        :return bool: True if record was removed
        """
        try:
            del self.records[desktop_file]
            return True
        except KeyError:
            return False

    def put(self, rec):
        """
        :param str rec['name']:
        :param str rec['description']:
        :param str rec['desktop_file']:
        :param str rec['icon']:
        """
        self.records[rec['name']] = rec

    def find(self, name, limit=9, min_score=0):
        """
        :param str name: name to search for
        :param int limit: max number of results
        :param int min_score: min score for search results [0..100]
        """
        return map(lambda i: i[0],
                   process.extractBests(name, self.records.values(),
                                        processor=lambda i: i['name'], limit=limit, score_cutoff=min_score))
