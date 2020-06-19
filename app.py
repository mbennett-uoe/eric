from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import UUIDType
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class Object(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    #uuid = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    uuid = db.Column(UUIDType(binary=True), default=uuid.uuid4, unique=True, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('object_type.id'), nullable=False)
    type = db.relationship('ObjectType', backref=db.backref('objects', lazy=True))
    primary_id = db.Column(db.String(64))


class ObjectType(db.Model):
    __tablename__ = 'object_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    url_construct = db.Column(db.String(256), nullable=True)


class Identifier(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    object_id = db.Column(db.Integer, db.ForeignKey('object.id'), nullable=False)
    object = db.relationship('Object', backref=db.backref('identifiers', lazy=True))
    type_id = db.Column(db.Integer, db.ForeignKey('identifier_type.id'), nullable=False)
    type = db.relationship('IdentifierType', backref=db.backref('identifiers', lazy=True))


class IdentifierType(db.Model):
    __tablename__ = 'identifier_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    url_construct = db.Column(db.String(256), nullable=True)


@app.route('/')
def index():
    return 'Welcome to ERIC!'


if __name__ == '__main__':
    app.run()
