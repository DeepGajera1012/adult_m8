from flask import Blueprint, jsonify, request, g
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
import os


admin_bp = Blueprint('admin', __name__)

print("dfbfbfbfbfvbfbvfgbfbfgbfgbfb")
print("dfbfbfbfbfvbfbvfgbfbfgbfgbfb")
print("dfbfbfbfbfvbfbvfgbfbfgbfgbfb")
print("dfbfbfbfbfvbfbvfgbfbfgbfgbfb")
print("dfbfbfbfbfvbfbvfgbfbfgbfgbfb")
print("dfbfbfbfbfvbfbvfgbfbfgbfgbfb")
print("dfbfbfbfbfvbfbvfgbfbfgbfgbfb")
print("dfbfbfbfbfvbfbvfgbfbfgbfgbfb")
print("dfbfbfbfbfvbfbvfgbfbfgbfgbfb")

def is_admin(user_id):
    cur = g.db.cursor()
    cur.execute(f"select role from tbl_users where id={user_id}")
    user = cur.fetchone()
    if user:
        if user[0] == 'admin':
            return True
        return False


@admin_bp.get("/verification_user_list")
@jwt_required() 
def verification_user_list():
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db. cursor(dictionary=True)
    cur.execute("select * from tbl_profile_verify where is_active=1")
    user_list = cur.fetchall()
    return jsonify({"user_list":user_list}),200
    
@admin_bp.put("/verify_user/<user_id>")
@jwt_required()
def verify_user(user_id):
    current_user_id = get_jwt_identity()
    if not is_admin(current_user_id):
        return jsonify({"error":"unauthrized access"}),401
    
    cur = g.db. cursor()
    cur.execute(f"update tbl_profile_verify set is_active=0 where user_id={user_id}")
    cur.execute(f"update tbl_users set is_profile_verify=1 where id={user_id}")
    g.db.commit()
    
    return jsonify({"message":"user profile verified"}),200
    