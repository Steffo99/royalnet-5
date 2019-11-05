# Imports go here!
from .version import VersionStar


# Enter the PageStars of your Pack here!
available_page_stars = [
    VersionStar,
]

# Enter the ExceptionStars of your Pack here!
available_exception_stars = [

]

# Don't change this, it should automatically generate __all__
__all__ = [star.__name__ for star in [*available_page_stars, *available_exception_stars]]
