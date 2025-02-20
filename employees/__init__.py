from flask import Blueprint

employees_bp = Blueprint('employees_bp', __name__)
from . import routes
