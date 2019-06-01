import flask as f


bp = f.Blueprint("helloworld", __name__, url_prefix="/helloworld")


@bp.route("/")
def helloworld():
    return "Hello world!"
