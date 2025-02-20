from flask import Blueprint

leaves_bp = Blueprint('leaves_bp', __name__)
from . import routes
