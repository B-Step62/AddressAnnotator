from enum import Enum

ERASE = "<ERASE>"


class EnterMode(Enum):
    IDLE = 1
    TEXT_SELECT = 2
    LABEL_SELECT = 3


CHAR_LABEL_SEPARATOR = "|"
