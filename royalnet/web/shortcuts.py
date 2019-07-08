import flask as f


def error(code, reason):
    return f.render_template("error.html", title=f"Errore {code}", reason=reason), code
