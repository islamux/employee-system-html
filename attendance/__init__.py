from flask import Blueprint

attendance_bp = Blueprint('attendance_bp', __name__)
from . import routes
