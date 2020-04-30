from .errors import ConfigurationError


class ConfigDict(dict):
    def __missing__(self, key):
        raise ConfigurationError(f"Missing config key '{key}'")

    @classmethod
    def convert(cls, item):
        if isinstance(item, dict):
            cd = ConfigDict()
            for key in item:
                cd[key] = cls.convert(item[key])
            return cd
        elif isinstance(item, list):
            nl = []
            for obj in item:
                nl.append(cls.convert(obj))
        else:
            return item
