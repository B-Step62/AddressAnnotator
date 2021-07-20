from typing import Dict, List, Tuple

from constants import CHAR_LABEL_SEPARATOR


class CharLabelReader:

    def __init__(self, addresses, labels):
        self._addresses = addresses
        self._labels = labels

    def __len__(self):
        return len(self._addresses)

    def read_record(self, index: int) -> Tuple[str, List[str]]:
        return self._addresses[index], self._labels[index]

    @staticmethod
    def from_file(path: str):
        with open(path, "r") as f:
            lines = f.readlines()
        addresses, labels = [], []
        for i, line in enumerate(lines):
            if i % 3 == 0:
                addresses.append(line.strip())
            elif i % 3 == 1:
                label = line.strip().split(CHAR_LABEL_SEPARATOR)
                assert len(addresses[-1]) == len(label), \
                    f"Address and char label length should be the same!\n" \
                    f"  Address: {addresses[-1]} with length {len(addresses[-1])}\n" \
                    f"  Label: {label} with length {len(label)}."
                labels.append(label)
        return CharLabelReader(addresses, labels)





