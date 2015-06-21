import os


class Path(object):
    # cache for better performance
    __cached_existing_path = None

    def __init__(self, query):
        self._path = os.path.expandvars(os.path.expanduser(query.lstrip()))

    def __str__(self):
        return self._path

    def exists(self):
        return os.path.exists(self._path)

    def get_basename(self):
        return os.path.basename(self._path.rstrip('/'))

    def is_dir(self):
        return os.path.isdir(self._path)

    def get_user_path(self):
        result = self._path.rstrip('/')

        user_dir = os.path.expanduser('~')
        if result.startswith(user_dir):
            return result.replace(user_dir, '~', 1)

        return result

    def get_existing_path(self):
        """
        Returns path to the last dir that exists in the user's query
        Example:
            query = /home/aleksandr/projects/foo/bar
            result = /home/aleksandr/projects
            (assuming foo & bar do not exist)
        """
        if self.__cached_existing_path:
            return self.__cached_existing_path

        result = self._path
        while not os.path.exists(result) and result:
            result = os.path.dirname(result)

        # special case when dir ends with "/."
        # we want to return path without .
        # example: /bin/env/. -> /bin/env
        if result.endswith('/.'):
            result = result[:-2]

        if not result:
            raise InvalidPathError('Invalid path "%s"' % self._path)

        self.__cached_existing_path = result
        return result

    def get_search_part(self):
        """
        Returns remaining part of the query that goes after get_existing_path()
        """
        return self._path[len(self.get_existing_path()):].strip('/')


class InvalidPathError(RuntimeError):
    pass
