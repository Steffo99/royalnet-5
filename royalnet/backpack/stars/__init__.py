# Imports go here!
from .api_royalnet_version import ApiRoyalnetVersionStar
from .api_auth_login_royalnet import ApiAuthLoginRoyalnetStar
from .api_user_passwd import ApiUserPasswd
from .api_auth_token import ApiAuthTokenStar
from .api_user_get import ApiUserGetStar
from .api_user_list import ApiUserListStar
from .api_user_find import ApiUserFindStar
from .api_user_create import ApiUserCreateStar
from .docs import DocsStar

# Enter the PageStars of your Pack here!
available_page_stars = [
    ApiRoyalnetVersionStar,
    ApiAuthLoginRoyalnetStar,
    ApiUserPasswd,
    ApiAuthTokenStar,
    ApiUserGetStar,
    ApiUserListStar,
    ApiUserFindStar,
    ApiUserCreateStar,
    DocsStar,
]

# Don't change this, it should automatically generate __all__
__all__ = [star.__name__ for star in available_page_stars]
