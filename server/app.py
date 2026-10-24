#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema


class Signup(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'errors': ['Username and password are required.']}, 422

        try:
            user = User(
                username=username,
                image_url=data.get('image_url'),
                bio=data.get('bio'),
            )
            user.password_hash = password
            db.session.add(user)
            db.session.commit()
        except (IntegrityError, ValueError):
            db.session.rollback()
            return {'errors': ['Username already exists or is invalid.']}, 422

        session['user_id'] = user.id
        return UserSchema().dump(user), 201


class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': '401 Unauthorized'}, 401

        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {'error': '401 Unauthorized'}, 401

        return UserSchema().dump(user), 200


class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return UserSchema().dump(user), 200

        return {'error': '401 Unauthorized'}, 401


class Logout(Resource):
    def delete(self):
        if not session.get('user_id'):
            return {'error': '401 Unauthorized'}, 401

        session.pop('user_id', None)
        return '', 204


class RecipeIndex(Resource):
    def get(self):
        if not session.get('user_id'):
            return {'error': '401 Unauthorized'}, 401

        recipes = Recipe.query.order_by(Recipe.id).all()
        return RecipeSchema(many=True).dump(recipes), 200

    def post(self):
        if not session.get('user_id'):
            return {'error': '401 Unauthorized'}, 401

        data = request.get_json() or {}
        user = User.query.filter_by(id=session['user_id']).first()
        if not user:
            return {'error': '401 Unauthorized'}, 401

        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user=user,
            )
            db.session.add(recipe)
            db.session.commit()
        except (IntegrityError, ValueError):
            db.session.rollback()
            return {'errors': ['Recipe is invalid.']}, 422

        return RecipeSchema().dump(recipe), 201


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(port=5555, debug=True)