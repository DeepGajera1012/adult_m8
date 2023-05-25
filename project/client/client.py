from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity


client_bp = Blueprint('client', __name__)

@client_bp.get('/package')
@jwt_required()
def package():
    try:
        cursor = g.db.cursor(dictionary=True) 
        cursor.execute('SELECT price,name,descripation,fetures FROM tbl_package WHERE is_active=1 AND is_delete=0')
        user =cursor.fetchall()
        return jsonify({"Premium":user}),200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    


    