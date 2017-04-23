import os


class Path(object):
    # cache for better performance
    __cached_existing_dir = None

    def __init__(self, path):
        self._path = os.path.expandvars(os.path.expanduser(path.lstrip()))

    def get_abs_path(self):
        return self._path

    def exists(self):
        return os.path.exists(self._path)

    def get_basename(self):
        return os.path.basename(self._path.rstrip('/'))

    def get_dirname(self):
        return os.path.dirname(self.get_user_path())

    def is_dir(self):
        return os.path.isdir(self._path)

    def is_exe(self):
        return os.access(self._path, os.X_OK)

    def get_ext(self):
        return os.path.splitext(self._path)[1].lower()[1:]

    def get_user_path(self):
        result = self._path.rstrip('/')

        user_dir = os.path.expanduser('~')
        if result.startswith(user_dir):
            return result.replace(user_dir, '~', 1)

        return result

    def get_existing_dir(self):
        """
        Example (assuming foo & bar do not exist):

        >>> p = Path('/home/aleksandr/projects/foo/bar')
        >>> p.get_existing_dir() == '/home/aleksandr/projects'

        :returns: path to the last dir that exists in the user's query
        """
        if self.__cached_existing_dir:
            return self.__cached_existing_dir

        result = self._path
        while result and (not os.path.exists(result) or not os.path.isdir(result)):
            result = os.path.dirname(result)

        # special case when dir ends with "/."
        # we want to return path without .
        # example: /bin/env/. -> /bin/env
        if result.endswith('/.'):
            result = result[:-2]

        if not result:
            raise InvalidPathError('Invalid path "%s"' % self._path)

        self.__cached_existing_dir = result
        return result

    def get_search_part(self):
        """
        :returns: remaining part of the query that goes after :meth:`get_existing_dir`
        """
        return self._path[len(self.get_existing_dir()):].strip('/')


class InvalidPathError(RuntimeError):
    pass
