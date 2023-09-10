import os
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,current_app
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from car_app.customer import login_required
from car_app.db import get_db

bp = Blueprint('car', __name__)

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Function to get the path for uploaded files
def get_upload_path(filename):
    return os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

# Admin mode page, Admin can see all cars(booked and avalable)
@bp.route('/car/')
@login_required
def index():
    db = get_db()
    cars = db.execute(
        'SELECT id, name, seat, gearbox, image, model'
        ' FROM car'
        ' ORDER BY name ASC'
    ).fetchall()
    return render_template('admin/car_index.html', cars=cars)

# Car list
@bp.route('/available')
@login_required
def available():
    db = get_db()
    cars = db.execute(
        'SELECT id, name, seat, gearbox, image, model, door'
        ' FROM car'
        ' WHERE status = 1'
        ' ORDER BY name ASC'
    ).fetchall()
    return render_template('index.html', cars=cars)

# Guest mode page, Customer can see without logging in if he wish
@bp.route('/guest_mode')
def guest_mode():
    db = get_db()
    cars = db.execute(
        'SELECT id, name, seat, gearbox, image, model, door'
        ' FROM car'
        ' WHERE status = 1'
        ' ORDER BY name ASC'
    ).fetchall()
    return render_template('index.html', cars=cars)

## Admin can create new car entry ##
@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        name = request.form['name']
        model = request.form['model']
        status = request.form['status']
        seat = request.form['seat']
        door = request.form['door']
        gearbox = request.form['gearbox']
        image = request.files['image']
        error = None

        if not name:
            error = 'Name is required.'
        if not model:
            error = 'Model is required.'
        if not status:
            error = 'Status is required.'
        if not seat:
            error = 'Seat is required.'
        if not door:
            error = 'Door is required.'
        if not gearbox:
            error = 'Gearbox is required.'

        if error is not None:
            flash(error)
        else:
            # Check if an image was uploaded
            if image and allowed_file(image.filename):
                image_data = image.read()  # Read the binary image data

                db = get_db()
                db.execute(
                    'INSERT INTO car (name, model, status, seat, door, gearbox, image)'
                    ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (name, model, status, seat, door, gearbox, image_data)
                )
                db.commit()
                return redirect(url_for('car.admin_mode'))
            else:
                # Handle invalid or missing image
                flash('Invalid or missing image.')

    return render_template('admin/car_create.html')


# Getting a car associated with a given id to update it
def get_car(id, check_author=True):
    car = get_db().execute(
        'SELECT id, name, model, status, seat, door, gearbox, image'
        ' FROM car'
        ' WHERE car.id = ?',
        (id,)
    ).fetchone()

    if car is None:
        abort(404, f"Car id {id} doesn't exist.")

    return car

# Admin can update car details
@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    car = get_car(id)

    if request.method == 'POST':
        name = request.form['name']
        model = request.form['model']
        status = request.form['status']
        seat = request.form['seat']
        door = request.form['door']
        gearbox = request.form['gearbox']
        image = request.files['image']
        error = None

        if not name:
            error = 'Name is required.'
        if not model:
            error = 'Model is required.'
        if not status:
            error = 'Status is required.'
        if not seat:
            error = 'Seat is required.'
        if not door:
            error = 'Door is required.'
        if not gearbox:
            error = 'Gearbox is required.'

        if error is not None:
            flash(error)
        else:
            # Check if an image was uploaded
            if image and allowed_file(image.filename):
                image_data = image.read() 

                db = get_db()
                db.execute(
                    'UPDATE car SET name = ?, model = ?, status = ?, seat = ?, door = ?, gearbox = ?, image = ?'
                    'WHERE id = ?',
                    (name, model, status, seat, door, gearbox, image_data, id)
                )
                db.commit()
                return redirect(url_for('car.admin_mode'))
            else:
                # Handle invalid or missing image
                flash('Invalid or missing image.')
    return render_template('admin/car_update.html', car=car)

# Deletes the car with a given id
@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_car(id)
    db = get_db()
    db.execute('DELETE FROM car WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('car.index'))
