import typing

def cdj(class_: typing.Any) -> dict:
    """Return a dict of the class attributes without the ``__module__``, ``__dict__``, ``__weakref__`` and ``__doc__`` keys, to be used while generating dynamically SQLAlchemy declarative table classes.
    
    Parameters:
        class_: The object that you want to dict-ify. 

    Returns:
        The class dict.
        
    Warning:
        You can't dict-ify classes with ``__slots__``!"""
    d = dict(class_.__dict__)
    del d["__module__"]
    del d["__dict__"]
    del d["__weakref__"]
    del d["__doc__"]
    return d
