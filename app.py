from flask import Flask, jsonify, request, redirect, url_for, make_response, abort
from flask_sqlalchemy import SQLAlchemy
from flask_uuid import FlaskUUID
from sqlalchemy_utils import UUIDType
from sqlalchemy.orm import joinedload
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_ECHO'] = True
app.config['JSON_SORT_KEYS'] = False
db = SQLAlchemy(app)
FlaskUUID(app)


class Object(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(UUIDType(binary=False), default=uuid.uuid4, unique=True, nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('object_type.id'), nullable=False)
    type = db.relationship('ObjectType', lazy=False, backref=db.backref('objects', lazy=True))
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
    type = db.relationship('IdentifierType', lazy=False, backref=db.backref('identifiers', lazy=True))


class IdentifierType(db.Model):
    __tablename__ = 'identifier_type'
    id = db.Column(db.Integer, primary_key=True)
    shortcode = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(128), nullable=False)
    url_construct = db.Column(db.String(256), nullable=True)


def construct_url(url_format, id):
    if url_format and id:
        return url_format.replace("<id>", id)
    else:
        return None


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'status': 404, 'error': 'Not found'}), 404)


@app.route('/')
def index():
    return 'Welcome to ERIC!'


@app.route('/object/<int:object_id>')
@app.route('/resolve/<identifier>')
def redirect_id_to_uuid(object_id=None, identifier=None):
    if object_id:
        obj = Object.query.get_or_404(object_id)
        return redirect(url_for('view_object', uuid=obj.uuid))
    elif identifier:
        obj = Identifier.query.get_or_404(identifier)
        return redirect(url_for('view_object', uuid=obj.object.uuid))
    else:
        abort(404)


@app.route('/object/<uuid:uuid>')
def view_object(uuid):
    obj = Object.query.options(joinedload('identifiers')).filter(Object.uuid == uuid).first_or_404()
    obj_dict = {"id": obj.id,
                "uuid": obj.uuid,
                "type": obj.type.name,
                "primary_url": construct_url(obj.type.url_construct, obj.primary_id),
                "identifiers": [{"type": identifier.type.description,
                                 "shortcode": identifier.type.shortcode,
                                 "identifier": identifier.id,
                                 "url": construct_url(identifier.type.url_construct, identifier.id)}
                                for identifier in obj.identifiers]
                }
    return jsonify(obj_dict)


@app.route('/identifier/<identifier>')
def view_identifier(identifier):
    obj = Identifier.query.get_or_404(identifier)
    obj_dict = {"identifier": obj.id,
                "type": obj.type.description,
                "eric_uuid": obj.object.uuid,
                "eric_url": url_for('view_object', uuid=obj.object.uuid, _external=True),
                "url": construct_url(obj.type.url_construct, obj.id),
                }
    return jsonify(obj_dict)


@app.route('/convert/<identifier>/<desired_type>', endpoint="convert")
@app.route('/redirect/<identifier>/<desired_type>', endpoint="redirect")
def convert_identifier(identifier, desired_type):
    obj_subquery = Identifier.query.filter(Identifier.id == identifier).subquery()
    obj = Identifier.query.join(IdentifierType).filter(Identifier.object_id == obj_subquery.c.object_id)\
        .filter(IdentifierType.shortcode == desired_type).first_or_404()

    if request.endpoint == "redirect":
        return redirect(construct_url(obj.type.url_construct, obj.id))
    else:
        obj_dict = {"identifier": obj.id,
                    "type": obj.type.description,
                    "shortcode": obj.type.shortcode,
                    "url": construct_url(obj.type.url_construct, obj.id),
                    }
        return jsonify(obj_dict)


if __name__ == '__main__':
    app.run()
