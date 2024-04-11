from flask import render_template, request, redirect, url_for, flash, session
from app import app
from models import db, User, Section, Book, BookRequest
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
import os


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username=request.form.get('username')
    password=request.form.get('password')

    if not username or not password:
        flash('Please fill out all the fields!')
        return redirect(url_for('login'))
    
    user=User.query.filter_by(username=username).first()

    if not user:
        flash('Username does not exist!')
        return redirect(url_for('login'))
    
    if not check_password_hash(user.passhash, password):
        flash('Incorect password!')
        return redirect(url_for('login'))

    session['user_id'] = user.id
    flash('Login successful')
    
    return redirect(url_for('index'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    name = request.form.get('name')

    if not username or not password or not confirm_password:
        flash('Please fill out all fields')
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash('Passwords do not match!')
        return redirect(url_for('register'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists!')
        return redirect(url_for('register'))
    
    password_hash = generate_password_hash(password)
    
    new_user = User(username=username, passhash=password_hash, name=name)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('login'))
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_librarian:
            flash('You are not authorized to access this page')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

@app.route('/')
@auth_required
def index():
    user = User.query.get(session['user_id'])
    if user.is_librarian:
        return redirect(url_for('admin'))
    sections = Section.query.all()
    #return render_template('index.html', sections=sections)

    sname = request.args.get('sname') or ''
    bname = request.args.get('bname') or ''
    aname = request.args.get('aname') or ''
    #FIX THIS
    books=Book.query
    if sname:
        sections = Section.query.filter(Section.name.ilike(f'%{sname}%')).all()
    if bname:
        books = books.filter(Book.name.ilike(f'%{bname}%'))
    if aname:
        books = books.filter(Book.author.ilike(f'%{aname}%'))
    books = books.all()

    return render_template('index.html', sections=sections, sname=sname, bname=bname, aname=aname, books=books)

@app.route('/profile')
@auth_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')

    if not username or not cpassword or not password:
        flash('Please fill out all the required fields!')
        return redirect(url_for('profile'))

    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password!')
        return redirect(url_for('profile'))

    if username != user.username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists!')
            return redirect(url_for('profile'))

    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))

@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))

@app.route('/admin')
@admin_required
def admin():
    sections = Section.query.all()
    return render_template('admin.html', sections=sections)

@app.route('/section/add')
@admin_required
def add_section():
    return render_template('section/add.html')

@app.route('/section/add', methods=['POST'])
@admin_required
def add_section_post():
    name = request.form.get('name')
    description = request.form.get('description')
    #date_created = request.form.get('date_created')
    date_created = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    if not name:
        flash('Please fill out all fields')
        return redirect(url_for('add_section'))

    section = Section(name=name, description=description)

    db.session.add(section)
    db.session.commit()
    flash('Section added successfully')
    return redirect(url_for('admin'))


@app.route('/section/<int:id>/')
@admin_required
def show_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/show.html', section=section)

@app.route('/section/<int:id>/edit')
@admin_required
def edit_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/edit.html', section=section)

@app.route('/section/<int:id>/edit', methods=['POST'])
@admin_required
def edit_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    name = request.form.get('name')
    description = request.form.get('description')  
    if not name or not description:  
        flash('Please fill out all fields')
        return redirect(url_for('edit_section', id=id))
    section.name = name
    section.description = description  
    section.date_created = datetime.utcnow()  
    db.session.commit()
    flash('Section updated successfully')
    return redirect(url_for('admin'))

@app.route('/section/<int:id>/delete')
@admin_required
def delete_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/delete.html', section=section)

@app.route('/section/<int:id>/delete', methods=['POST'])
@admin_required
def delete_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    db.session.delete(section)
    db.session.commit()

    flash('Section deleted successfully')
    return redirect(url_for('admin'))

@app.route('/book/add/<int:section_id>')
@admin_required
def add_book(section_id):
    sections = Section.query.all()
    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))
    return render_template('book/add.html', section=section, sections=sections)

'''
@app.route('/book/add/', methods=['POST'])
@admin_required
def add_book_post():
    name = request.form.get('name')
    author = request.form.get('author')
    section_id = request.form.get('section_id')

    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))

    if not name or not author:
        flash('Please fill out all fields')
        return redirect(url_for('add_book', section_id=section_id))

    book = Book(name=name, section=section, author=author)
    db.session.add(book)
    db.session.commit()

    flash('Book added successfully')
    return redirect(url_for('show_section', id=section_id)) 
    '''

@app.route('/book/<int:id>/edit')
@admin_required
def edit_book(id):
    sections = Section.query.all()
    book = Book.query.get(id)
    return render_template('book/edit.html', sections=sections, book=book)

@app.route('/book/<int:id>/edit/', methods=['POST'])
@admin_required
def edit_book_post(id):
    name = request.form.get('name')
    author = request.form.get('author')
    section_id = request.form.get('section_id')

    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))

    if not name or not author:
        flash('Please fill out all fields')
        return redirect(url_for('add_book', section_id=section_id))


    book = Book.query.get(id)
    book.name = name
    book.author = author
    book.section_id=section_id
    
    db.session.commit()

    flash('Book edited successfully')
    return redirect(url_for('show_section', id=section_id))

@app.route('/book/<int:id>/delete')
@admin_required
def delete_book(id):
    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    return render_template('book/delete.html', book=book)

@app.route('/book/<int:id>/delete', methods=['POST'])
@admin_required
def delete_book_post(id):
    book = Book.query.get(id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    section_id = book.section.id
    db.session.delete(book)
    db.session.commit()

    flash('Book deleted successfully')
    return redirect(url_for('show_section', id=section_id))

'''
@app.route('/book_request/<int:book_id>', methods=['POST'])
@auth_required
def book_request(book_id):
    book = Book.query.get(book_id)
    if not book:
        flash('Book does not exist')
        return redirect(url_for('index'))
    
    user = session['user_id']

    book_request = BookRequest(
        user_id=user,
        book_id=book.id,
        request_date=datetime.now(),
        is_active=True  # By default, the request is active until approved or denied
    )

    db.session.add(book_request)
    db.session.commit()

    flash('Book request submitted successfully. Please wait for librarian approval.')
    return redirect(url_for('index'))
'''
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return dict(current_user=user)
    return dict(current_user=None)

@app.route('/request_book/<int:book_id>', methods=['POST'])
@auth_required
def request_book(book_id):
    book = Book.query.get(book_id)

    user = User.query.get(session['user_id'])
    if user.active_requests.count() >= 5:
        flash('You have reached the maximum number of active requests.')
        return redirect(url_for('index'))
    
    if book:
        user_id = session.get('user_id')
        user = User.query.get(user_id)

        if not user:
            flash('User not found')
            return redirect(url_for('index'))

        if book in user.books_issued:
            flash('You have already requested this book')
        else:
            user.books_issued.append(book)
            db.session.commit()

            book_request = BookRequest(
                user_id=user.id,
                book_id=book.id,
                request_date=datetime.now(),
                is_active=True
            )
            db.session.add(book_request)
            db.session.commit()
            
            flash('Book request submitted successfully')
    else:
        flash('Book not found')
    return redirect(url_for('index'))

@app.route('/approve_request/<int:request_id>', methods=['POST'])
@admin_required
def approve_request(request_id):
    request = BookRequest.query.get(request_id)
    if request:
        # Perform approval actions
        db.session.delete(request)
        db.session.commit()
        flash('Request approved')
    else:
        flash('Request not found')
    return redirect(url_for('requests'))

@app.route('/deny_request/<int:request_id>', methods=['POST'])
@admin_required
def deny_request(request_id):
    request = BookRequest.query.get(request_id)
    if request:
        # Perform denial actions
        db.session.delete(request)
        db.session.commit()
        flash('Request denied')
    else:
        flash('Request not found')
    return redirect(url_for('requests'))

@app.route('/my_requests')
@auth_required
def my_requests():
    user_requests = BookRequest.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_requests.html', user_requests=user_requests)

@app.route('/pending_requests')
@admin_required
def pending_requests():
    pending_requests = BookRequest.query.filter_by(is_active=True).all()
    return render_template('pending_requests.html', pending_requests=pending_requests)



ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/book/add/', methods=['POST'])
@admin_required
def add_book_post():
    name = request.form.get('name')
    author = request.form.get('author')
    section_id = request.form.get('section_id')

    section = Section.query.get(section_id)
    if not section:
        flash('Section does not exist')
        return redirect(url_for('admin'))

    if not name or not author:
        flash('Please fill out all fields')
        return redirect(url_for('add_book', section_id=section_id))

    if 'pdf_file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['pdf_file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File uploaded successfully')

        book = Book(name=name, author=author, section_id=section_id, pdf_path=filename)
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully')

        return redirect(url_for('show_section', id=section_id))

    else:
        flash('Invalid file format')
        return redirect(request.url)