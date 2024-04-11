from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime

db=SQLAlchemy(app)

user_book_association = db.Table('user_book_association',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'))
)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    passhash = db.Column(db.String(100), nullable=False)
    is_librarian = db.Column(db.Boolean, default=False)
    books_issued = db.relationship('Book', secondary=user_book_association, backref=db.backref('issued_to', lazy='dynamic'))
    active_requests = db.relationship('BookRequest', primaryjoin='and_(User.id==BookRequest.user_id, ''BookRequest.is_active==True)', backref='requester', lazy='dynamic')

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text) #!!!!!!!!!!!!!!CHANGE THIS!!!!!!!!!!!!!!!!!!!
    author = db.Column(db.String(100), nullable=False)
    pages = db.Column(db.Integer)  
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    pdf_path = db.Column(db.String(255))
    
    section = db.relationship('Section', backref=db.backref('books', lazy=True))


class BookRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    request_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_approved = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('book_requests', lazy=True))
    book = db.relationship('Book', backref=db.backref('book_requests', lazy=True))


with app.app_context():
    db.create_all()
    admin = User.query.filter_by(is_librarian=True).first()
    if not admin:
        password_hash = generate_password_hash('admin')
        admin = User(username='admin', passhash=password_hash, name='Admin', is_librarian=True)
        db.session.add(admin)
        db.session.commit()


