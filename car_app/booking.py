from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash

from car_app.customer import login_required
from car_app.db import get_db
from car_app.car import get_car

bp = Blueprint('booking', __name__, url_prefix='/booking')


# Admin can see all bookings
@bp.route('/')
@login_required
def index():
    db = get_db()
    bookings = db.execute(
        'SELECT b.id, ca.name, cu.name, cu.last_name, start_date, end_date'
        ' FROM booking b'
        ' JOIN customer cu ON b.customer_id = cu.id'
        ' JOIN car ca on b.car_id = ca.id'
        ' ORDER BY start_date ASC'
    ).fetchall()
    return render_template('admin/booking_index.html', bookings=bookings)

# Customer can see his own bookings
@bp.route('/my_bookings')
@login_required
def my_bookings():
    db = get_db()
    # Get the customer_id of the logged-in user
    customer_id = g.customer['id']

    # Modify the SQL query to filter by customer_id
    bookings = db.execute(
        'SELECT b.id, ca.name, cu.name, cu.last_name, start_date, end_date'
        ' FROM booking b'
        ' JOIN customer cu ON b.customer_id = cu.id'
        ' JOIN car ca ON b.car_id = ca.id'
        ' WHERE b.customer_id = ?'
        ' ORDER BY start_date ASC',
        (customer_id,)
    ).fetchall()

    return render_template('booking/index.html', bookings=bookings)



@bp.route('/create/<int:car_id>', methods=('GET', 'POST'))
@login_required
def create(car_id):
    car = get_car(car_id)
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        error = None

        if not start_date:
            error = 'Start date is required.'
        if not end_date:
            error = 'End date is required.'

        if error is not None:
            flash(error)
        else:
            customer_id = g.customer['id']

            db = get_db()
            db.execute(
                'INSERT INTO booking (car_id, customer_id, start_date, end_date)'
                ' VALUES (?, ?, ?, ?)',
                (car_id, customer_id, start_date, end_date)
            )
            db.commit()
            return redirect(url_for('booking.my_bookings'))

    return render_template('booking/create.html', car=car)

# Getting booking with the same booking id
def get_booking(id, check_author=True):
    booking = get_db().execute(
        'SELECT b.id, cu.name, ca.name, start_date, end_date, b.customer_id'
        ' FROM booking b'
        ' JOIN customer cu ON b.customer_id = cu.id'
        ' JOIN car ca on b.car_id = ca.id'
        ' WHERE b.id = ?',
        (id,)
    ).fetchone()
    if booking is None:
        abort(404, f"Booking id {id} doesn't exist.")

    # Check if the user is an admin (role == 1) or if the booking belongs to the user
    if g.customer['role'] == 1 or (check_author and booking['customer_id'] == g.customer['id']):
        return booking
    else:
        abort(403)

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    booking = get_booking(id)

    if request.method == 'POST':
        car_id = request.form['car_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        error = None

        if not car_id:
            error = 'Select car.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE booking SET car_id = ?, start_date = ?, end_date = ?, customer_id'
                ' WHERE id = ?',
                (car_id, start_date, end_date, g.customer['id'], id)
            )
            db.commit()
            return redirect(url_for('booking.my_bookings'))

    return render_template('booking/update.html', booking=booking)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_booking(id)
    db = get_db()
    db.execute('DELETE FROM booking WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('booking.my_bookings'))
