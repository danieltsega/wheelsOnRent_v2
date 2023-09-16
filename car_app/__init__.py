import os

from flask import Flask, send_from_directory, url_for, send_file, Response, render_template, redirect
from car_app.db import get_db


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    @app.route('/uploads/<int:car_id>')
    def uploaded_image(car_id):
        # Fetch the image data from the database
        db = get_db()
        result = db.execute(
            'SELECT image FROM car WHERE id = ?', (car_id,)).fetchone()

        if result is not None:
            image_data = result['image']
            # Return the image data as a response
            return Response(image_data, content_type='image/jpeg')

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'car_app.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/')
    def home():
        return render_template('home.html')
        # return redirect(url_for('car.guest_mode'))

    from . import db
    db.init_app(app)

    from . import customer
    app.register_blueprint(customer.bp)

    from . import booking
    app.register_blueprint(booking.bp)

    from . import car
    app.register_blueprint(car.bp)
    app.add_url_rule('/', endpoint='index')

    return app
