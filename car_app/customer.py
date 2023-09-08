import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash

from car_app.db import get_db

bp = Blueprint('customer', __name__, url_prefix='/customer')

# Customer register control
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        name = request.form['name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        password = request.form['password']
        role = int(request.form['role'])
        db = get_db()
        error = None

        if not name:
            error = 'Name is required.'
        elif not last_name:
            error = 'Last Name is required.'
        elif not phone_number:
            error = 'Phone Number is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO customer (name, last_name, phone_number, email,  password, role) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, last_name, phone_number, email, generate_password_hash(password), role),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("customer.login"))

        flash(error)

    return render_template('customer_register.html')

# Customer login control
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        customer = db.execute(
            'SELECT * FROM customer WHERE email = ?', (email,)
        ).fetchone()

        if customer is None:
            error = 'Incorrect email.'
        elif not check_password_hash(customer['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['customer_id'] = customer['id']
            if customer['role'] == 1:
                return redirect(url_for('customer.admin_dashboard'))
            return redirect(url_for('car.index'))

        flash(error)

    return render_template('customer_login.html')

# Getting customer id that was previously stored during login
@bp.before_app_request
def load_logged_in_customer():
    customer_id = session.get('customer_id')

    if customer_id is None:
        g.customer = None
    else:
        g.customer = get_db().execute(
            'SELECT * FROM customer WHERE id = ?', (customer_id,)
        ).fetchone()

# logging out a customer by clearing customer id from the session
@bp.route('/logout')
def logout():
    # Clear the user's session data
    session.pop('customer_id', None)
    return redirect(url_for('home'))

# Use the after_request decorator to add a response header
@bp.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# login_required decorator for login requirin views
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.customer is None:
            return redirect(url_for('customer.login'))

        return view(**kwargs)

    return wrapped_view


## Admin control over customer ##

# Customer index page
@bp.route('/')
@login_required
def index():
    db = get_db()
    customers = db.execute(
        'SELECT id, name, last_name, email, phone_number'
        ' FROM customer'
        ' WHERE role = 0'
        ' ORDER BY name ASC'
    ).fetchall()
    return render_template('admin/customer_index.html', customers=customers)

# customer can be created by the logged in addmin
@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        password = request.form['password']
        role = int(request.form['role'])
        db = get_db()
        error = None

        if not name:
            error = 'Name is required.'
        elif not last_name:
            error = 'Last Name is required.'
        elif not phone_number:
            error = 'Phone Number is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO customer (name, last_name, phone_number, email,  password, role) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, last_name, phone_number, email, generate_password_hash(password), role),
                )
                db.commit()
            except db.IntegrityError:
                error = f"Email {email} is already registered."
            else:
                return redirect(url_for("customer.index"))

        flash(error)

    return render_template('customer_create.html')

## Admin can update customer table ##
# Get the customer to be updated
def get_customer(id, check_author=True):
    customer = get_db().execute(
        'SELECT id, name, last_name, phone_number, email,  password'
        ' FROM customer'
        ' WHERE id = ?',
        (id,)
    ).fetchone()

    if customer is None:
        abort(404, f"Customer id {id} doesn't exist.")

    return customer

# Update the customer
@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    customer = get_customer(id)
    if request.method == 'POST':
        name = request.form['name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        email = request.form['email']
        password = request.form['password']
        role = int(request.form['role'])
        error = None

        if not name:
            error = 'Name is required.'
        elif not last_name:
            error = 'Last Name is required.'
        elif not phone_number:
            error = 'Phone Number is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'


        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE customer SET name = ?, last_name = ?, phone_number = ?, email = ?,  password = ?, role = ?'
                ' WHERE id = ?',
                (name, last_name, phone_number, email,  password, role, id)
            )
            db.commit()
            return redirect(url_for('customer.index'))

    return render_template('customer_update.html', customer=customer)

@bp.route('/edit_profile', methods=('GET', 'POST'))
@login_required
def edit_profile():
    if request.method == 'POST':
        name = request.form['name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        error = None

        if not name:
            error = 'Name is required.'
        elif not last_name:
            error = 'Last Name is required.'
        elif not email:
            error = 'Email is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'

        if error is None:
            db = get_db()
            db.execute(
                'UPDATE customer SET name = ?, last_name = ?, email = ?, password = ? WHERE id = ?',
                (name, last_name, email, generate_password_hash(password), g.customer['id'])
            )
            db.commit()
            flash('Profile updated successfully.')
            return redirect(url_for('customer.admin_dashboard'))

        flash(error)

    return render_template('admin/admin_update.html')



@bp.route('/<int:id>/delete', methods=('POST', 'DELETE',))
@login_required
def delete(id):
    get_customer(id)
    db = get_db()
    db.execute('DELETE FROM customer WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('customer.index'))

# Admin Home(Dashboard)
@bp.route('/admin_dashboard')
@login_required
def admin_dashboard():
# Connect to the database
    db = get_db()

    # SQL queries to count records in each table
    car_count = db.execute('SELECT COUNT(*) FROM car').fetchone()[0]
    customer_count = db.execute('SELECT COUNT(*) FROM customer').fetchone()[0]
    booking_count = db.execute('SELECT COUNT(*) FROM booking').fetchone()[0]

    # Render the dashboard template and pass counts as context
    return render_template('admin/admin_dashboard.html',
                           car_count=car_count,
                           customer_count=customer_count,
                           booking_count=booking_count)






