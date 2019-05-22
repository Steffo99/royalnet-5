class Data:
    """Royalnet data. All fields in this class will be converted to a dict when about to be sent."""
    def __init__(self):
        pass

    def to_dict(self):
        return self.__dict__
