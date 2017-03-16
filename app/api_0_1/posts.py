from . import api
from ..models import Post, Permission
from flask import request, jsonify, url_for, current_app, g
from .. import db
from .authentication import auth
from .decorators import permission_required
from .errors import forbidden


@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE_ARTICLES)
def new_post():
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json(), 201,
                   {'location': url_for('api.get_post', id=post.id, _external=True)})


# @api.route('/post/')
# @auth.login_required
# def get_posts():
#     posts = Post.query.all()
#     return jsonify({'posts': [post.to_json() for post in posts]})


@api.route('/posts/<int:id>')
@auth.login_required
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())


@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user is not post.id \
            and not g.current_user.can(Permission.ADMINISTER):
        return forbidden('Insufficient permissions')
    post.body = request.json.get('body', post.body)
    db.session(post)
    db.session.commit()
    return jsonify(post.to_json)


@api.route('/posts/')
# @permission_required(Permission.ADMINISTER)
@auth.login_required
def get_posts():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page+1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page+1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total})


@api.route('/get_user_followed_posts/<int:id>')
@auth.login_required
def get_user_followed_posts(id):
    pass