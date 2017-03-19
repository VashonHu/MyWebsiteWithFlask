#!/usr/bin/python

from app import create_app, db
from app.models import User, Role, Permission, Question, Comment, Vote
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
import os

app = create_app('default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role,
                Question=Question, Permission=Permission, Comment=Comment, Vote=Vote)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("db", MigrateCommand)


@manager.command
def test():
    import unittest
    tests = unittest.TestLoader().discover('tests')#tests is dir
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    from app import db
    from app.models import User, Role, Question, Answer, Comment, Vote

    # db.drop_all()
    # db.create_all()
    # db.session.commit()
    # Role.insert_roles()
    #
    # User.generate_fake()
    # User.add_self_follows()
    Question.generate_fake()
    Answer.generate_fake()
    Comment.generate_fake()
    Vote.generate_fake()

    # db.session.commit()


def detect():
    Role.insert_roles()

if __name__ == '__main__':
    manager.run()
    detect()
