"""A User Games Wiki viewer :py:class:`royalnet.web.Royalprint`. Doesn't support any kind of edit."""

import flask as f
import os
from ...royalprint import Royalprint
from ...shortcuts import error, from_urluuid
from royalnet.packs.common.tables import User
from royalnet.packs.royal.tables import WikiPage, WikiRevision
from ....utils.wikirender import prepare_page_markdown, RenderError


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("wikiview", __name__, url_prefix="/wiki/view", template_folder=tmpl_dir,
                required_tables={User, WikiPage, WikiRevision})


def prepare_page(page):
    try:
        if page.format == "markdown":
            return f.render_template("wikiview_page.html",
                                     page=page,
                                     parsed_contents=f.Markup(prepare_page_markdown(page.contents)),
                                     css=page.css)
        elif page.format == "html":
            return f.render_template("wikiview_page.html",
                                     page=page,
                                     parsed_contents=f.Markup(page.contents),
                                     css=page.css)
        else:
            return error(500, f"Non esiste nessun handler in grado di preparare pagine con il formato {page.format}.")
    except RenderError as e:
        return error(500, f"La pagina Wiki non può essere preparata a causa di un errore: {str(e)}")


@rp.route("/")
def wikiview_index():
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    pages = sorted(alchemy_session.query(alchemy.WikiPage).all(), key=lambda page: page.title)
    return f.render_template("wikiview_index.html", pages=pages)


@rp.route("/<page_id>", defaults={"title": ""})
@rp.route("/<page_id>/<title>")
def wikiview_by_id(page_id: str, title: str):
    page_uuid = from_urluuid(page_id)
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    page = alchemy_session.query(alchemy.WikiPage).filter(alchemy.WikiPage.page_id == page_uuid).one_or_none()
    if page is None:
        return error(404, f"La pagina richiesta non esiste.")
    return prepare_page(page)
