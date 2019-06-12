"""Some Royalprints that can be used with the Royalnet Flask server."""

from .home import rp as rp_home
from .wikiview import rp as rp_wikiview
from .tglogin import rp as rp_tglogin

__all__ = ["rp_home", "rp_wikiview", "rp_tglogin"]
