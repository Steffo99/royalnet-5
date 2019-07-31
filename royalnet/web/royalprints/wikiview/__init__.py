"""A Royal Games Wiki viewer :py:class:`royalnet.web.Royalprint`. Doesn't support any kind of edit."""

import flask as f
import markdown2
import re
import os
from ...royalprint import Royalprint
from ...shortcuts import error, from_urluuid
from ....database.tables import Royal, WikiPage, WikiRevision


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("wikiview", __name__, url_prefix="/wiki/view", template_folder=tmpl_dir,
                required_tables={Royal, WikiPage, WikiRevision})


class WikiRenderError(Exception):
    """An error occurred while trying to render the wiki page."""


def prepare_page_markdown(page):
    if list(page.content).count(">") > 99:
        raise WikiRenderError("Too many nested quotes")
    converted_md = markdown2.markdown(page.content.replace("<", "&lt;"),
                                      extras=["spoiler", "tables", "smarty-pants", "fenced-code-blocks"])
    converted_md = re.sub(r"{https?://(?:www\.)?(?:youtube\.com/watch\?.*?&?v=|youtu.be/)([0-9A-Za-z-]+).*?}",
                          r'<div class="youtube-embed">'
                          r'   <iframe src="https://www.youtube-nocookie.com/embed/\1?rel=0&amp;showinfo=0"'
                          r'           frameborder="0"'
                          r'           allow="autoplay; encrypted-media"'
                          r'           allowfullscreen'
                          r'           width="640px"'
                          r'           height="320px">'
                          r'   </iframe>'
                          r'</div>', converted_md)
    converted_md = re.sub(r"{https?://clyp.it/([a-z0-9]+)}",
                          r'<div class="clyp-embed">'
                          r'    <iframe width="100%" height="160" src="https://clyp.it/\1/widget" frameborder="0">'
                          r'    </iframe>'
                          r'</div>', converted_md)
    return f.Markup(converted_md)


def prepare_page(page):
    try:
        if page.format == "markdown":
            return f.render_template("wikiview_page.html",
                                     page=page,
                                     parsed_content=f.Markup(prepare_page_markdown(page)),
                                     css=page.css)
        elif page.format == "html":
            return f.render_template("wikiview_page.html",
                                     page=page,
                                     parsed_content=f.Markup(page.content),
                                     css=page.css)
        else:
            return error(500, f"Non esiste nessun handler in grado di preparare pagine con il formato {page.format}.")
    except WikiRenderError as e:
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
