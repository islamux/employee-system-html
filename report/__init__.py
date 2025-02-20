from flask import Blueprint

report_bp = Blueprint('report_bp', __name__)
from . import routes
