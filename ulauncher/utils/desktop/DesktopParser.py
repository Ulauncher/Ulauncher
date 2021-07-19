import os


class DesktopParser:
    DESKTOP_SECTION = '[Desktop Entry]'

    __property_list = None

    def __init__(self, filename):
        self.__property_list = []
        self.set_filename(filename)
        self.read()
        super().__init__()

    def set_filename(self, filename):
        self._filename = filename

    def read(self):
        """
        Read [Desktop Entry] section and save key=values pairs to __property_list
        """
        with open(self._filename, 'r') as f:
            is_desktop_section = False
            for line in f.readlines():
                line = line.strip(' ' + os.linesep)
                if line == self.DESKTOP_SECTION:
                    is_desktop_section = True
                    continue
                if line.startswith('['):
                    # another section begins
                    is_desktop_section = False
                    continue
                if is_desktop_section and '=' in line:
                    (key, value) = line.split('=', 1)
                    self.set(key.strip(), value.strip())

    def write(self):
        """
        Write properties to the file
        """
        dir = os.path.dirname(self._filename)
        if not os.path.exists(dir):
            os.makedirs(dir)

        with open(self._filename, 'w') as f:
            f.write(os.linesep.join((self.DESKTOP_SECTION, os.linesep.join(['='.join((str(k), str(v).strip()))
                                                                            for k, v in self.__property_list]))))

    def get(self, name):
        """
        Raises KeyError if name is not found
        """

        for key, value in self.__property_list:
            if key.lower() == name.lower():
                return value
        raise KeyError('%s' % name)

    def set(self, name, value):
        if not name:
            raise ValueError("Invalid value for name: '%s'" % name)

        for i, (key, _) in enumerate(self.__property_list):
            if key.lower() == name.lower():
                self.__property_list[i] = (key, value)
                return

        self.__property_list.append((name, value))

    def get_boolean(self, name):
        """
        Returns True if value is "1", "yes", "true", or "on"

        Returns False if value is "0", "no", "false", or "off"

        String values are checked in a case-insensitive manner.

        Any other value will cause it to raise ValueError.
        """

        value = self.get(name).lower()
        if value in ("1", "yes", "true", "on"):
            return True
        if value in ("0", "no", "false", "off"):
            return False

        raise ValueError("Cannot coerce '%s' to boolean" % value)
