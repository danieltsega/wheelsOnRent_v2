import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash, generate_password_hash

from car_app.db import get_db

bp = Blueprint('home', __name__, url_prefix='/')


@bp.route('/')
def index():
    return render_template('home.html')
