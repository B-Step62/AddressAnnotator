from typing import Dict, List


class CSVReader:

    def __init__(self, header: List[str], contents: List[Dict[str, str]]):
        self._header = header
        self._contents = contents

    def get_header(self) -> List[str]:
        return self._header

    def read_record(self, index: int) -> Dict[str, str]:
        return self._contents[index]

    def __len__(self):
        return len(self._contents)

    @staticmethod
    def from_file(path: str, sep: str, header=None):
        with open(path, "r") as f:
            lines = f.readlines()

            if header is None:
                header = [col for col in lines[0].strip().split(sep)]
                lines = lines[1:]

            contents = []
            for line in lines:
                values = line.split(sep)
                assert len(header) == len(values), \
                    f"Malformed line doesn't match header schema!\nHeader: {header}\nLine: {line}"
                content = {label.strip(): token.strip() for label, token in zip(header, values)}
                contents.append(content)
        return CSVReader(header, contents)





