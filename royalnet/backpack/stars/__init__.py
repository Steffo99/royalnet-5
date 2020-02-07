# Imports go here!
from .api_royalnet_version import ApiRoyalnetVersionStar
from .api_login_royalnet import ApiLoginRoyalnetStar
from .api_token_info import ApiTokenInfoStar


# Enter the PageStars of your Pack here!
available_page_stars = [
    ApiRoyalnetVersionStar,
    ApiLoginRoyalnetStar,
    ApiTokenInfoStar,
]

# Don't change this, it should automatically generate __all__
__all__ = [star.__name__ for star in available_page_stars]
