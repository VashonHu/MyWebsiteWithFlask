from . import api
from ..models import Question, Permission
from flask import request, jsonify, url_for, current_app, g
from .. import db
from .authentication import auth
from .decorators import permission_required
from .errors import forbidden


@api.route('/questions/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_question():
    question = Question.from_json(request.json)
    question.author = g.current_user
    db.session.add(question)
    db.session.commit()
    return jsonify(question.to_json(), 201,
                   {'location': url_for('api.get_question', id=question.id, _external=True)})


# @api.route('/question/')
# @auth.login_required
# def get_questions():
#     questions = Question.query.all()
#     return jsonify({'questions': [question.to_json() for question in questions]})


@api.route('/questions/<int:id>')
@auth.login_required
def get_question(id):
    question = Question.query.get_or_404(id)
    return jsonify(question.to_json())


@api.route('/questions/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_question(id):
    question = Question.query.get_or_404(id)
    if g.current_user is not question.id \
            and not g.current_user.can(Permission.ADMINISTER):
        return forbidden('Insufficient permissions')
    question.body = request.json.get('body', question.body)
    db.session(question)
    db.session.commit()
    return jsonify(question.to_json)


@api.route('/questions/')
# @permission_required(Permission.ADMINISTER)
@auth.login_required
def get_questions():
    page = request.args.get('page', 1, type=int)
    pagination = Question.query.paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'],
        error_out=False)
    questions = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_questions', page=page+1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_questions', page=page+1, _external=True)
    return jsonify({
        'questions': [question.to_json() for question in questions],
        'prev': prev,
        'next': next,
        'count': pagination.total})


@api.route('/get_user_followed_questions/<int:id>')
@auth.login_required
def get_user_followed_questions(id):
    pass