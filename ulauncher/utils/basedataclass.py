# This is a more compact alternative to JsonData, which does not require using decorators
#
# It works slightly differently by looping through the class props of the class and all inherited classes
# and setting them for the instance in __init__
# It also needs to use __getattribute__ instead of __getattr__
#
# TODO(friday): try to migrate the methods from JsonData here. # noqa: TD003
# Should be able to move stringify and save_as here and
# replace __json_value_blacklist__ and __json_sort_keys__ with params
# But don't migrate "new_from_file" and "save"


class BaseDataClass(dict):
    def __init__(self, **kwargs):
        super().__init__()
        # add defaults from parent classes in inheritance order
        for cls in reversed(self.__class__.__mro__):
            if cls in BaseDataClass.__mro__:
                continue
            defaults = {
                k: v for k, v in vars(cls).items() if (not k.startswith("__") and not callable(getattr(cls, k)))
            }
            self.update(defaults)

        # set values
        self.update(**kwargs)

    def __dir__(self):  # For IDE autocompletion
        return dir(type(self)) + list(self.keys())

    def __delattr__(self, name):
        del self[name]

    def __getattribute__(self, key):
        try:
            return self[key]
        except KeyError:
            return super().__getattribute__(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __setitem__(self, key, value):
        if hasattr(self.__class__, key):
            if key.startswith("__"):
                msg = f'Invalid property "{key}". Must not override class property.'
                raise KeyError(msg)

            class_val = getattr(self.__class__, key)
            if callable(class_val):
                msg = f'Invalid property "{key}". Must not override class method.'
                raise KeyError(msg)
            if not isinstance(value, type(class_val)):
                msg = f'"{key}" must be of type {type(class_val).__name__}, {type(value).__name__} given.'
                raise KeyError(msg)

        super().__setitem__(key, value)

    # Make sure everything flows through __setitem__
    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
