def classdictjanitor(class_) -> dict:
    """Return the cleaned class attributes in a dict."""
    d = dict(class_.__dict__)
    del d["__module__"]
    del d["__dict__"]
    del d["__weakref__"]
    del d["__doc__"]
    return d
