from flask import Blueprint, jsonify, request, g
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import pyotp
from datetime import datetime,timedelta



auth_bp = Blueprint('auth', __name__)



