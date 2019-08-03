"""A :py:class:`royalnet.web.Royalprint` to create and award :py:class:`royalnet.database.tables.Medal`s."""

import flask as f
import os
import typing
from ...royalprint import Royalprint
from ...shortcuts import error
from ....database.tables import *
from ....utils.wikirender import prepare_page_markdown, RenderError


# Maybe some of these tables are optional...
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("medals", __name__, url_prefix="/medals", template_folder=tmpl_dir,
                required_tables={Royal, ActiveKvGroup, Alias, Diario, Discord, Keygroup, Keyvalue, Telegram, WikiPage,
                                 WikiRevision, Bio})


@rp.route("/create", methods=["GET", "POST"], defaults={"medal_id": None})
@rp.route("/<int:medal_id>/edit", methods=["GET", "POST"])
def medal_edit(medal_id: typing.Optional[int]):
    ...


@rp.route("/<int:medal_id>/award", methods=["GET", "POST"])
def medal_award(medal_id: int):
    ...
