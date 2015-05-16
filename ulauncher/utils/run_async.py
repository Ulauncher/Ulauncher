from threading import Thread
from functools import wraps


def run_async(*args, **kwargs):
    """
        run_async(func)
            function decorator, intended to make "func" run in a separate
            thread (asynchronously).
            Returns the created Thread object

            E.g.:
            @run_async
            def task1():
                do_something

            @run_async(daemon=True)
            def task2():
                do_something_too

            t1 = task1()
            t2 = task2()
            ...
            t1.join()
            t2.join()
    """
    daemon = kwargs.get('daemon', False)

    def _run_async(func):
        @wraps(func)
        def async_func(*args, **kwargs):
            func_hl = Thread(target=func, args=args, kwargs=kwargs)
            func_hl.setDaemon(daemon)
            func_hl.start()
            return func_hl

        return async_func

    if len(args) == 1 and not kwargs and callable(args[0]):
        # No arguments, this is the decorator
        # Set default values for the arguments
        return _run_async(args[0])
    else:
        # This is just returning the decorator
        return _run_async
