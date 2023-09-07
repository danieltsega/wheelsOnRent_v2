from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash

from car_app.customer import login_required
from car_app.db import get_db

bp = Blueprint('booking', __name__, url_prefix='/booking')

# Booking index page(The logged in user can see his reservation)
@bp.route('/')
@login_required
def index():
    db = get_db()
    boookings = db.execute(
        'SELECT b.id, cu.name, cu.last_name, ca.name, start_date, end_date'
        ' FROM booking b'
        ' JOIN customer cu ON b.customer_id = cu.id'
        ' JOIN car ca on b.car_id = ca.id'
        ' ORDER BY start_date ASC'
    ).fetchall()
    return render_template('admin/booking_index.html', boookings=boookings)


@bp.route('/create/<int:car_id>', methods=('GET', 'POST'))
@login_required
def create(car_id):
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
            customer_id = session.get('customer_id')

            db = get_db()
            db.execute(
                'INSERT INTO booking (car_id, customer_id, start_date, end_date)'
                ' VALUES (?, ?, ?, ?)',
                (car_id, customer_id, start_date, end_date)
            )
            db.commit()
            return redirect(url_for('customer.index'))


    db = get_db()
    car = db.execute(
        'SELECT id, name, seat, gearbox, image, model'
        ' FROM car WHERE id = ?',
        (car_id,)
    ).fetchone()

    return render_template('booking_create.html', car=car)

# Getting booking with the same booking id
def get_booking(id, check_author=True):
    booking = get_db().execute(
        'SELECT b.id, cu.name, ca.name, start_date, end_date'
        ' FROM booking b'
        ' JOIN customer cu ON b.customer_id = cu.id'
        ' JOIN car ca on b.car_id = ca.id'
        ' WHERE booking.id = ?',
        (id,)
    ).fetchone()

    if booking is None:
        abort(404, f"Booking id {id} doesn't exist.")

    if check_author and g.customer and booking['customer_id'] != g.customer['id']:
        abort(403)
    elif check_author and not g.customer and g.customer['role'] == 1:
        abort(403)
    elif not check_author or g.customer and g.customer['role'] == 1 or g.customer == booking['customer_id']:
        return booking

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
            return redirect(url_for('booking.index'))

    return render_template('booking_update.html', booking=booking)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_booking(id)
    db = get_db()
    db.execute('DELETE FROM booking WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('booking.index'))
