from . import api
from ..models import Question, Permission
from flask import request, jsonify, url_for, current_app
from .. import db
from .authentication import auth
from .decorators import permission_required
from .errors import forbidden


@api.route('/get_user/<int:id>')
@auth.login_required
def get_user(id):
    pass