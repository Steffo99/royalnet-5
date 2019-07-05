"""A Royal Games Wiki viewer :py:class:`royalnet.web.Royalprint`. Doesn't support any kind of edit."""

import flask as f
import markdown2
import re
import uuid
import os
from ... import Royalprint
from ....database.tables import Royal, WikiPage, WikiRevision


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
rp = Royalprint("wikiview", __name__, url_prefix="/wiki/view", template_folder=tmpl_dir,
                required_tables={Royal, WikiPage, WikiRevision})


def prepare_page_markdown(page):
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
        return "Format not available", 500


@rp.route("/")
def wikiview_index():
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    pages = sorted(alchemy_session.query(alchemy.WikiPage).all(), key=lambda page: page.title)
    return f.render_template("wikiview_index.html", pages=pages)


@rp.route("/<uuid:page_id>", defaults={"title": ""})
@rp.route("/<uuid:page_id>/<title>")
def wikiview_by_id(page_id: uuid.UUID, title: str):
    alchemy, alchemy_session = f.current_app.config["ALCHEMY"], f.current_app.config["ALCHEMY_SESSION"]
    page = alchemy_session.query(alchemy.WikiPage).filter(alchemy.WikiPage.page_id == page_id).one_or_none()
    if page is None:
        return "No such page", 404
    return prepare_page(page)
