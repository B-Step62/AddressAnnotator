from typing import Dict, List

from parser.crf_parser import CRFParser
from utils.csv_reader import CSVReader


class CSVReaderWrapperWithWeakEstimator:

    def __init__(self, csv_reader: CSVReader):
        self._csv_reader = csv_reader
        self._estimator = CRFParser()

    def get_header(self) -> List[str]:
        return self._csv_reader.get_header()

    def read_record(self, index: int, estimate: bool = True) -> Dict[str, str]:
        record = self._csv_reader.read_record(index)
        if estimate:
            parsed_result = {k.lower(): v for k, v in self._estimator.parse(record["address"]).items()}
            for key in parsed_result:
                if key not in record:  # Use existing one
                    record[key] = parsed_result[key.lower()]
        return record

    def __len__(self):
        return len(self._csv_reader)

    @staticmethod
    def from_file(path: str, sep: str, header=None):
        csv_reader = CSVReader.from_file(path=path, sep=sep, header=header)
        return CSVReaderWrapperWithWeakEstimator(csv_reader)





