from abs import ABCMeta, abstractmethod

class DummyParser(metaclass=ABCMeta):
    """
    Dummy parser class. You can implement any parser as long as it has parse() method.
    """
    def __init__(self):
        pass

    @abstractmethod
    def parse(self, address):
        pass 
