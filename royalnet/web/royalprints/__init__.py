"""Some Royalprints that can be used with the Royalnet Flask server."""

from . import home
from . import wikiview
from . import tglogin
from . import docs
from . import wikiedit
from . import mcstatus
from . import diarioview
from . import profile
from . import login
from . import newaccount

rp_home = home.rp
rp_wikiview = wikiview.rp
rp_tglogin = tglogin.rp
rp_docs = docs.rp
rp_wikiedit = wikiedit.rp
rp_mcstatus = mcstatus.rp
rp_diarioview = diarioview.rp
rp_profile = profile.rp
rp_login = login.rp
rp_newaccount = newaccount.rp

__all__ = ["rp_home", "rp_wikiview", "rp_tglogin", "rp_docs", "rp_wikiedit", "rp_mcstatus", "rp_diarioview",
           "rp_profile", "rp_login", "rp_newaccount"]
