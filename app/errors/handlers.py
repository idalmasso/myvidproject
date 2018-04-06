from app.errors import bp
from flask import render_template


@bp.app_errorhandler(404)
def not_found_error(error):
    print(error)
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def server_error(error):
    print(error)
    return render_template('errors/500.html'), 500
