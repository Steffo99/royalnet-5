# Imports go here!
from .api_royalnet_version import ApiRoyalnetVersionStar
from .api_login_royalnet import ApiLoginRoyalnetStar
from .api_token_info import ApiTokenInfoStar
from .api_token_passwd import ApiTokenPasswdStar
from .api_token_create import ApiTokenCreateStar
from .api_user_get import ApiUserGetStar
from .api_user_list import ApiUserListStar
from .api_user_find import ApiUserFindStar
from .api_alias_list import ApiAliasListStar
from .docs import DocsStar

# Enter the PageStars of your Pack here!
available_page_stars = [
    ApiRoyalnetVersionStar,
    ApiLoginRoyalnetStar,
    ApiTokenInfoStar,
    ApiTokenPasswdStar,
    ApiTokenCreateStar,
    ApiUserGetStar,
    ApiUserListStar,
    ApiUserFindStar,
    ApiAliasListStar,
    DocsStar,
]

# Don't change this, it should automatically generate __all__
__all__ = [star.__name__ for star in available_page_stars]
