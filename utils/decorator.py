from constants import EnterMode


def mode(enter_mode: EnterMode):
    def _mode(func):
        def wrapper(self, *args, **kwargs):
            if self._enter_mode == enter_mode:
                return func(self, *args, **kwargs)
        return wrapper
    return _mode
