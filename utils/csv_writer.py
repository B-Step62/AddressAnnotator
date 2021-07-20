import csv
from typing import Dict, List


class CSVWriter:

    def __init__(self, path: str, sep: str, header=None):
        self._path = path
        self._sep = sep
        self._header = header

        with open(self._path, "w") as f:
            writer = csv.DictWriter(f, fieldnames=self._header, delimiter=self._sep)
            if self._header is not None:
                writer.writeheader()

    def append_list(self, _list: List[str]):
        assert len(self._header) == len(_list),\
            f"Cannot write row which doesn't match header schema!\n  Header: {self._header}  Row: {_list}"
        with open(self._path, "a") as f:
            writer = csv.writer(f, delimiter=self._sep)
            writer.writerow(_list)

    def append_dict(self, _dict: Dict[str, str]):
        assert set(self._header) == set(_dict.keys()),\
            f"Cannot write row which doesn't match header schema!\n  Header: {self._header}  Row: {_dict}"
        with open(self._path, "a") as f:
            writer = csv.DictWriter(f, fieldnames=self._header, delimiter=self._sep)
            writer.writerow(_dict)
