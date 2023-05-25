from flask import Blueprint, jsonify, request, g
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import pyotp
from datetime import datetime,timedelta



authentication_bp = Blueprint('auth',__name__)

app=Flask(__name__)



def send_email(users):
    from project import mail
    otp=random.randint(1000,9999)
    if users:        
        user_id=users[0]
        msg = Message("Verification email", sender="jaybthakkar2305@gmail.com", recipients=['jaybthakkar2305@gmail.com'])
        msg.body = f"{otp} is your OTP for user verification."
        mail.send(msg)
        cursor=g.db.cursor()
        cursor.execute(f"INSERT INTO tbl_otp(user_id,otp) VALUES('{user_id}','{otp}')")
        g.db.commit()
        return "user ragister successfully"
    return "user not found"
    
    

@authentication_bp.post('/register')
def register():
    try:
        data=request.json
        role=data.get('role')
        profile_image=request.files.get('profile_image')
        first_name=data.get('first_name')
        last_name=data.get('last_name')
        username=data.get('username')
        email=data.get('email')
        phone=data.get('phone')


        if role not in ['escort' , 'client']:
            return jsonify({'error':'invalid role'}),400
        if not first_name:
            return jsonify({'error':'please enter first_name'}),400
        if not last_name:
            return jsonify({'error':'please enter last_name'}),400
        if not username:
            return jsonify({'error':'please enter username'})
        if not email:
            return jsonify({'error':'please enter email'}),400
        if not phone:
            return jsonify({'error':'please enter phone number'}),400       
        
        
        cursor=g.db.cursor()
        cursor.execute(f"SELECT * from tbl_users where email='{email}'")
        users=cursor.fetchone()
        if not users:
            cursor=g.db.cursor(buffered=True)
            cursor.execute(f"INSERT INTO tbl_users(role,first_name,last_name,username,email,phone) VALUES('{role}','{first_name}','{last_name}','{username}','{email}','{phone}' )")
            g.db.commit()
            cursor=g.db.cursor()
            cursor.execute(f"SELECT * from tbl_users where email='{email}' ORDER BY email DESC")
            users=cursor.fetchone()
            a = send_email(users)
            return jsonify({"msg":a}),200
        return jsonify({'message':'user already exist'}),400

    
    except Exception as e:
        return jsonify({'error':str(e)}),400

@authentication_bp.post('/create_password/<user_id>')
def create_password(user_id):
    data=request.json
    password=data.get('password')
    cursor=g.db.cursor(buffered=True)
    cursor.execute(f"SELECT * FROM `tbl_users` where id ={user_id}")
    user=cursor.fetchone()  

    if user:
        cursor=g.db.cursor(buffered=True)
        pwd_hash = generate_password_hash(password,method='sha256',salt_length=8)
        cursor.execute(f"UPDATE tbl_users SET password = '{pwd_hash}' WHERE id = {user_id};")
        g.db.commit()

        
        return jsonify({'successfull':'password added successfully'})
    return jsonify({'error':'Wrong credentital'}),401      

   




@authentication_bp.post('/login')
def login():
    try:
        email=request.json.get('name')
        password=request.json.get('password')
        if not email:
            return jsonify({'error':'please enter email'}),400  
        if not password:
            return jsonify({'error':'please enter password'}),400  
        print(email,password)
        cursor=g.db.cursor()
        cursor.execute(f"SELECT * FROM tbl_users WHERE email = '{email}' and is_verify=1")
        user = cursor.fetchone()
        print(user)
        if user:
            is_pass_correct= (user[2],password)
            print(is_pass_correct)
            if is_pass_correct:
                access=create_access_token(identity=user[0])
                return jsonify({
                    'user':{
                        'access':access,
                        'email':user[4]
                    }
                }),200
            else:
                return jsonify({'error':'Wrong credentital'}),401 
        else:
            return jsonify({'error':'Wrong credentital'}),401 
        return jsonify({'message':'login done'}),401 
    except Exception as e:
        return jsonify({'error':str(e)}),400
    

@authentication_bp.post('/verify_otp/<user_id>')
def verifyotp(user_id):
    try:
        data=request.json
        otp=data.get('otp')
        if not otp:
            return jsonify({'error':'otp required'}),400
        cursor=g.db.cursor()
        cursor.execute(f"SELECT otp,id FROM tbl_otp WHERE user_id = {user_id} and is_active=1 ORDER by id DESC LIMIT 1")
        res=cursor.fetchone()
        if res:
            if int(otp) != int(res[0]):
                return jsonify({'message':'otp not match'})
            cursor.execute(f"update tbl_otp set is_active=0 where id={res[1]}")
            cursor.execute(f"update tbl_users set is_verify=1 where id={user_id}")
            g.db.commit()
            return jsonify({"successfull":"user is verified"})
        else:
            return jsonify({"message":"otp not verified"})
        return jsonify({"error":"enter valid otp"})
    except Exception as e:
        return jsonify({'error':str(e)}),400

     


@authentication_bp.post('/reset_password/<hash_email>/<users_id>')
def reset_password(hash_email,users_id):
    try:
        cursor=g.db.cursor()
        cursor.execute(f"select * from tbl_users where id={users_id}")
        user=cursor.fetchone()
        if user:
            is_email=check_password_hash(hash_email,user[6])
            if is_email:
                new_password=request.json.get('new_password')
                if new_password:
                    hash_password=generate_password_hash(new_password,method='sha256',salt_length=8)
                    cursor.execute(f"UPDATE `tbl_users` SET `password`='{hash_password}' where `id`={user[0]}")
                    g.db.commit()
                    return jsonify({"message":"password is updeted"}),200
                return jsonify({"error":"enter valid password"}),400
            return jsonify({"error":"email is not valid"}),400
        return jsonify({"error":"user not found"}),400
    except Exception as e:
        return jsonify({'error':str(e)}),400

    
@authentication_bp.post('/forget_password')
def forget_password():        
    data = request.json
    email = data.get('email') 
    if not email:
            return jsonify({'error':'email required'}),400     
    cursor = g.db.cursor()
    cursor.execute(f"SELECT * FROM tbl_users WHERE email='{email}'")
    user = cursor.fetchone()

    if user:
        from project import mail
        hash_email = generate_password_hash(email, method='sha256', salt_length=8)
        print(hash_email)
        a = hash_email
        b = user[0]
        msg = Message('Hello', sender='jaybthakkar2305@gmail.com', recipients=['jaybthakkar2305@gmail.com'])
        msg.body = f"Click here to reset password: http://127.0.0.1:5000/reset_password/{a}/{b}"
        mail.send(msg)
        
        # Store user_id & Token into ResetPassword Table

        print(f"'{hash_email}'/'{user[0]}'")
        return jsonify({"message": "Email sent successfully"}), 200

    return jsonify({"error": "Enter a valid email"}), 400


@authentication_bp.post('/add_interest/<users_id>')
def add_interest(users_id):
    data = request.json
    interest = data.get('interest') 
    cursor = g.db.cursor()
    cursor.execute(f"SELECT * FROM tbl_users WHERE id={users_id}")
    user = cursor.fetchone()

    if user:
        cursor = g.db.cursor(buffered=True)
        for interest in interest:
            cursor.execute(f"INSERT INTO tbl_user_interests (user_id, interest) VALUES ({users_id}, '{interest}')")
        g.db.commit()

        return jsonify({'successful': 'Interests added successfully'})
    return jsonify({'error': 'Wrong credential'}), 401 
        


@authentication_bp.post('/change_password/<users_id>')
def change_password(users_id):
    try:
        cursor = g.db.cursor()
        cursor.execute(f"SELECT password FROM tbl_users WHERE id={users_id}")
        user = cursor.fetchone()
        print("asdrftghjkhuygtfdresdrfghbnjmkjnhbgvfcdxzsdxcfvgbhnm",user)


        if user:
            old_password = request.json.get('old_password')
            new_password = request.json.get('new_password')
            print(old_password)
            print(new_password)
            

            if old_password and new_password:
                if check_password_hash(user[0],old_password):
                    hash_password = generate_password_hash(new_password, method='sha256', salt_length=8)
                    cursor.execute(f"UPDATE tbl_users SET password='{hash_password}' WHERE id={users_id}")
                    g.db.commit()
                    return jsonify({"message": "Password updated successfully"}), 200
                else:
                    return jsonify({"error": "Incorrect old password"}), 400
            else:
                return jsonify({"error": "Please provide both old and new passwords"}), 400
        else:
            return jsonify({"error": "User not found"}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


