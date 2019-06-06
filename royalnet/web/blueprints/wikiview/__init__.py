import flask as f
import markdown2
import re
import uuid
import os
from ... import Royalprint
from ....database.tables import Royal, WikiPage, WikiRevision


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
bp = Royalprint("wikiview", __name__, url_prefix="/wikiview", template_folder=tmpl_dir,
                required_tables={Royal, WikiPage, WikiRevision})


def prepare_page(page):
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
    return converted_md


@bp.route("/")
def wikiview_index():
    from ...alchemyhandler import alchemy, alchemy_session
    pages = alchemy_session.query(alchemy.WikiPage).all()
    return f.render_template("wikiview_index.html", pages=pages)


@bp.route("/id/<page_id>")
def wikiview_by_id(page_id: str):
    from ...alchemyhandler import alchemy, alchemy_session
    page_uuid = uuid.UUID(page_id)
    page = alchemy_session.query(alchemy.WikiPage).filter(alchemy.WikiPage.page_id == page_uuid).one_or_none()
    if page is None:
        return "No such page", 404
    parsed_content = prepare_page(page)
    return f.render_template("wikiview_page.html", page=page, parsed_content=f.Markup(parsed_content))


@bp.route("/title/<title>")
def wikiview_by_title(title: str):
    from ...alchemyhandler import alchemy, alchemy_session
    page = alchemy_session.query(alchemy.WikiPage).filter(alchemy.WikiPage.title == title).one_or_none()
    if page is None:
        return "No such page", 404
    parsed_content = prepare_page(page)
    return f.render_template("wikiview_page.html", page=page, parsed_content=f.Markup(parsed_content))
