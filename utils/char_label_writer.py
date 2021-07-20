from typing import Dict, List

from constants import CHAR_LABEL_SEPARATOR


class CharLabelWriter:

    def __init__(self, path: str):
        self._path = path
        # Clean up file
        with open(self._path, "w") as f:
            f.write("")

    def append(self, address: str, labels: List[str]):
        assert len(address) == len(labels),\
            f"Cannot write row whose address length and label length don't match!\n  Address: {address}  Labels: {labels}"
        with open(self._path, "a") as f:
            f.write(address + "\n")
            f.write(CHAR_LABEL_SEPARATOR.join(labels) + "\n")
            f.write("\n")
