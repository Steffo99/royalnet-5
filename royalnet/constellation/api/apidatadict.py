from .apierrors import MissingParameterException


class ApiDataDict(dict):
    def __missing__(self, key):
        raise MissingParameterException(f"Missing '{key}'")
