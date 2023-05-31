from flask import Blueprint, jsonify, request, g,render_template,redirect,session,send_file
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
import os


admin_bp = Blueprint('admin', __name__)


def is_admin(user_id):
    cur = g.db.cursor()
    cur.execute(f"select role from tbl_users where id={user_id}")
    user = cur.fetchone()
    if user:
        if user[0] == 'admin':
            return True
        return False


@admin_bp.route("/admin_login",methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        user_pass = request.form.get('password')
        cur = g.db.cursor()
        print(email,user_pass)
        cur.execute(f"select * from tbl_users where email='{email}' and password='{user_pass}'")
        user = cur.fetchone()
        print(user)
        if user:
            # session['user'] = email
            return redirect('/index')
            # access=create_access_token(identity=user[0])
        return render_template('login.html' ,error_message={'message':'user name or password is worng'})
    return render_template('login.html')

@admin_bp.route("/display_escort",methods=['GET'])
def display_escort():
    cur = g.db.cursor()
    cur.execute(f"select id,first_name,last_name,username,email,phone,dob,address from tbl_users where role='escort' and is_active=1 and is_delete=0 ")
    escort_data = cur.fetchall()
    return render_template('display_users.html',data=escort_data)

@admin_bp.route("/display_client",methods=['GET'])
def display_client():
    cur = g.db.cursor()
    cur.execute(f"select id,first_name,last_name,username,email,phone,dob,address from tbl_users where role='client' and is_active=1 and is_delete=0 ")
    escort_data = cur.fetchall()
    return render_template('display_users.html',data=escort_data)


@admin_bp.route("/edit_record/<id>",methods=['GET','POST'])
def edit_record(id):
    cur = g.db.cursor()
    if request.method == 'POST':
        form_data = request.form
        fname = form_data.get("fname")
        lname = form_data.get("lname")
        uname = form_data.get("username")
        email = form_data.get("email")
        mobile = form_data.get("mobile")
        dob = form_data.get("dob")
        address = form_data.get("address")
        cur.execute(f"update tbl_users set first_name='{fname}',last_name='{lname}',username='{uname}',email='{email}',phone='{mobile}',dob='{dob}',address='{address}' where id={id} ")
        # cur.execute(f"insert into tbl_users (first_name,last_name,username,email,phone,dob,address) values ('{fname}','{lname}','{uname}','{email}','{mobile}','{dob}','{address}')")
        g.db.commit()
        return redirect("/index")

    cur.execute(f"select id,first_name,last_name,username,email,phone,dob,address from tbl_users where id={id} and is_active=1 and is_delete=0")
    data = cur.fetchone()
    if not data:
        return redirect("/index")

    return render_template('edit_details.html',data=data)

@admin_bp.route("/delete_record/<id>",methods=['GET','POST'])
def delete_record(id):
    cur = g.db.cursor()
    cur.execute(f"update tbl_users set is_active=0 and is_delete=1 where id={id}")
    g.db.commit()
    return redirect("/index")

# @admin_bp.post("/verify_login")
# def verify_login():
#     email = request.form.get('email')
#     user_pass = request.form.get('password')
#     cur = g.db.cursor()
#     print(email,user_pass)
#     cur.execute(f"select * from tbl_users where email='{email}' and password='{user_pass}' and role='admin'")
#     user = cur.fetchone()
#     print(user)
#     if user:
#         # session['user'] = email
#         return redirect('/index')
#         # access=create_access_token(identity=user[0])
#     return render_template('login.html' ,error_message={'message':'user name or password is worng'})
    
    

@admin_bp.get("/index")
def index():
    data = {}
    cur = g.db.cursor()
    cur.execute("select count(id) from tbl_users where role='client' and is_active=1 and is_delete=0")
    client_count = cur.fetchone()
    data['client']=client_count[0]
    cur.execute("select count(id) from tbl_users where role='escort' and is_active=1 and is_delete=0")
    escort_count = cur.fetchone()
    data['escort']=escort_count[0]
    cur.execute("select count(id) from tbl_escort_video")
    video_count = cur.fetchone()
    data['video']=video_count[0]
    cur.execute("select count(id) from tbl_escort_image")
    image_count = cur.fetchone()
    data['image']=image_count[0]
    # print(data)
    return render_template('index.html',data=data)


@admin_bp.get("/display_videos")
def disply_videos():
    cur = g.db.cursor(dictionary=True)
    cur.execute("select ev.id,ev.video,ev.titel,ev.price,ev.descripation,u.username from tbl_escort_video ev join tbl_users u on ev.escort_id = u.id where ev.is_active=1 and ev.is_delete=0")
    video_data = cur.fetchall()
    print(cur.fetchall())
    return render_template("display_video.html",data=video_data)

@admin_bp.get("/display_images")
def display_images():
    cur = g.db.cursor(dictionary=True)
    cur.execute("select ei.id,u.username,ei.image from tbl_escort_image ei join tbl_users u on ei.escort_id = u.id where ei.is_active=1 and ei.is_delete=0")
    image_data = cur.fetchall()
    print(cur.fetchall())
    return render_template("display_img.html",data=image_data)



@admin_bp.get("/verification_user_list")
# @jwt_required() 
def verification_user_list():
    # current_user_id = get_jwt_identity()
    # if not is_admin(current_user_id):
    #     return jsonify({"error":"unauthrized access"}),401
    cur = g.db. cursor(dictionary=True)
    cur.execute("select * from tbl_profile_verify where is_active=1")
    user_list = cur.fetchall()
    return render_template("verify_user.html",data=user_list)
    # return jsonify({"user_list":user_list}),200
    
@admin_bp.get("/verify_user/<user_id>")
# @jwt_required()
def verify_user(user_id):
    # current_user_id = get_jwt_identity()
    # if not is_admin(current_user_id):
    #     return jsonify({"error":"unauthrized access"}),401
    
    cur = g.db. cursor()
    cur.execute(f"update tbl_profile_verify set is_active=0 where user_id={user_id}")
    cur.execute(f"update tbl_users set is_profile_verify=1 where id={user_id}")
    g.db.commit()
    return redirect('/verification_user_list')
    
    # return jsonify({"message":"user profile verified"}),200

@admin_bp.get("/decline_request/<user_id>")
# @jwt_required()
def decline_request(user_id):
    # current_user_id = get_jwt_identity()
    # if not is_admin(current_user_id):
    #     return jsonify({"error":"unauthrized access"}),401
    
    cur = g.db. cursor()
    cur.execute(f"update tbl_profile_verify set is_active=0 where user_id={user_id}")
    g.db.commit()
    return redirect('/verification_user_list')
    

@admin_bp.route('/display_media/<media_name>',methods=['GET','POST'])
def display(media_name):
    return send_file(os.path.join(f'media/{media_name}'))