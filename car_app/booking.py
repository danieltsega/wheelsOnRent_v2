from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash

from car_app.customer import login_required
from car_app.db import get_db
from car_app.car import get_car
from car_app.shared_variables import get_greeting, get_today_date

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
    # Say Good Morning/Good Afternoon your customer
    greeting = get_greeting()

    db = get_db()
    # Get the customer_id of the logged-in user
    customer_id = g.customer['id']

    # Modify the SQL query to filter by customer_id
    bookings = db.execute(
        'SELECT b.id, car_id, ca.id, ca.name, customer_id, cu.id, cu.name, cu.last_name, start_date, end_date'
        ' FROM booking b'
        ' JOIN customer cu ON customer_id = cu.id'
        ' JOIN car ca ON car_id = ca.id'
        ' WHERE customer_id = ?'
        ' ORDER BY start_date ASC',
        (customer_id,)
    ).fetchall()

    return render_template('booking/index.html', greeting=greeting, bookings=bookings)


@bp.route('/create/<int:car_id>', methods=('GET', 'POST'))
@login_required
def create(car_id):
    today_date = get_today_date()
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
            db.execute(
                'UPDATE car SET status = 0 WHERE id = ?',
                (car_id,)
            )
            db.commit()
            return redirect(url_for('booking.my_bookings'))

    return render_template('booking/create.html', today_date=today_date, car=car)

# Getting booking with the same booking id
def get_booking(id, check_author=True):
    booking = get_db().execute(
        'SELECT b.id, cu.id, customer_id, cu.name, ca.id, car_id, ca.name, start_date, end_date'
        ' FROM booking b'
        ' JOIN customer cu ON customer_id = cu.id'
        ' JOIN car ca ON car_id = ca.id'
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
    #car = get_car(car_id)
    db = get_db()
    cars = db.execute(
        'SELECT id, name, model, seat, door, gearbox, image, price'
        ' FROM car'
        ' ORDER BY name ASC'
    ).fetchall()

    #for item in cars:
        #car = item

    if request.method == 'POST':
        if 'update' in request.form:
            car_id = request.form['car_id']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
        elif 'cancel' in request.form:
            return redirect(url_for('booking.my_bookings'))
        error = None

        if not start_date:
            error = 'Start date is required.'
        if not end_date:
            error = 'End date is required.'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE booking SET car_id = ?, start_date = ?, end_date = ?, customer_id = ?'
                ' WHERE id = ?',
                (car_id, start_date, end_date, g.customer['id'], id)
            )
            db.commit()
            return redirect(url_for('booking.my_bookings'))

    return render_template('booking/update.html', booking=booking, cars=cars)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    booking = get_booking(id)
    car_id = booking['car_id']  # Get the car_id associated with this booking
    db = get_db()
    db.execute('DELETE FROM booking WHERE id = ?', (id,))
    db.execute('UPDATE car SET status = 1 WHERE id = ?', (car_id,))  # Update car status to 1 (available)
    db.commit()
    if g.customer['role'] == 1:
        return redirect(url_for('booking.index'))
    return redirect(url_for('booking.my_bookings'))


# This is a function to run periodicaly to check expired bookings
# To delete them
# This should be run at least once per a day
# This is an alternative automation if the customer or admin did not delete the expired booking
@bp.route('/check_and_update_car_status')
def check_and_update_car_status():
    # This route checks for cars with end dates that have passed
    # and updates their status to 1 (available for rent)

    today_date = get_today_date()

    db = get_db()

    # Step 1: Update car status
    expired_cars = db.execute(
        'SELECT id FROM booking WHERE end_date < ?',
        (today_date,)
    ).fetchall()

    for car_id in expired_cars:
        db.execute(
            'UPDATE car SET status = 1 WHERE id = ?',
            (car_id,)
        )

    # Step 2: Delete expired bookings
    db.execute(
        'DELETE FROM booking WHERE end_date < ?',
        (today_date,)
    )

    db.commit()

    return 'Car statuses updated and expired bookings deleted.'
