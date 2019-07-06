"""Some Royalprints that can be used with the Royalnet Flask server."""

from .home import rp as rp_home
from .wikiview import rp as rp_wikiview
from .tglogin import rp as rp_tglogin
from .docs import rp as rp_docs
from .wikiedit import rp as rp_wikiedit
from .mcstatus import rp as rp_mcstatus
from .diarioview import rp as rp_diarioview
from .profile import rp as rp_profile

__all__ = ["rp_home", "rp_wikiview", "rp_tglogin", "rp_docs", "rp_wikiedit", "rp_mcstatus", "rp_diarioview", "rp_profile"]
