from flask import Blueprint, jsonify, request, g
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import random
from datetime import datetime,timedelta



authentication_bp = Blueprint('auth',__name__)





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
    
 #-----------------------------------------register------------------------------------   

@authentication_bp.post('/register')
def register():
    try:
        data=request.json
        role=data.get('role')
        first_name=data.get('first_name')
        last_name=data.get('last_name')
        username=data.get('username')
        email=data.get('email')
        phone=data.get('phone')
        address=data.get('address')
        latitude=data.get('latitude')
        longitude=data.get('longitude')

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
        if not address:
            return jsonify({'error':'please enter address'})
        if not latitude:
            return jsonify({'error':'please enter latitude'}),400
        if not longitude:
            return jsonify({'error':'please enter longitude'}),400                  
        cursor=g.db.cursor()
        cursor.execute(f"SELECT * from tbl_users where email='{email}'")
        users=cursor.fetchone()
        if not users:
            cursor=g.db.cursor(buffered=True)
            cursor.execute(f"INSERT INTO tbl_users(role,first_name,last_name,username,email,phone,address,latitude,longitude) VALUES('{role}','{first_name}','{last_name}','{username}','{email}','{phone}', '{address}','{latitude}','{longitude}' )")
            g.db.commit()
            cursor=g.db.cursor()
            cursor.execute(f"SELECT * from tbl_users where email='{email}' ORDER BY email DESC")
            users=cursor.fetchone()
            a = send_email(users)
            return jsonify({"msg":a}),200
        return jsonify({'message':'user already exist'}),400    
    except Exception as e:
        return jsonify({'error':str(e)}),400

#--------------------------------------------login----------------------------------------

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
    

#--------------------------------------------verify_otp----------------------------------------


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


#--------------------------------------------forget_password----------------------------------------

    
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
        a = hash_email
        b = user[0]
        msg = Message('Hello', sender='jaybthakkar2305@gmail.com', recipients=['jaybthakkar2305@gmail.com'])
        msg.body = f"Click here to reset password: http://127.0.0.1:5000/reset_password/{a}/{b}"
        mail.send(msg)       
        return jsonify({"message": "Email sent successfully"}), 200

    return jsonify({"error": "Enter a valid email"}), 400


#--------------------------------------------change_password----------------------------------------


@authentication_bp.post('/change_password/<users_id>')
def change_password(users_id):
    try:
        cursor = g.db.cursor()
        cursor.execute(f"SELECT password FROM tbl_users WHERE id={users_id}")
        user = cursor.fetchone()

        if user:
            old_password = request.json.get('old_password')
            new_password = request.json.get('new_password')
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



#--------------------------------------------add_user_data----------------------------------------



@authentication_bp.post('/add_user_data/<user_id>')
def add_user_data(user_id):
    data = request.json
    dob_str = data.get('dob')
    password = data.get('password')
    interests = data.get('interests')

    try:
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    cursor = g.db.cursor(buffered=True)
    cursor.execute(f"SELECT * FROM `tbl_users` WHERE id = {user_id}")
    user = cursor.fetchone()

    if user:
        cursor = g.db.cursor(buffered=True)
        pwd_hash = generate_password_hash(password, method='sha256', salt_length=8)
        cursor.execute(f"UPDATE tbl_users SET dob = '{dob}', password = '{pwd_hash}' WHERE id = {user_id};")

        if interests:
            for interest in interests:
                cursor.execute(f"INSERT INTO tbl_user_interests (user_id, interest) VALUES ({user_id}, '{interest}')")
        
        g.db.commit()

        return jsonify({'successful': 'User data added successfully'})

    return jsonify({'error': 'Wrong credentials'}), 401

#--------------------------------------------escort_personal_info----------------------------------------


@authentication_bp.post('/escort_personal_info/<user_id>')
def escort_personal_info(user_id):
    data = request.json
    gender = data.get('gender')
    bio = data.get('bio')

    valid_genders = ['male', 'female', 'transmale', 'transfemale', 'binary', 'nonbinary']
    
    if gender not in valid_genders:
        return jsonify({'error': 'Invalid gender. Please provide a valid gender.'}), 400

    cursor = g.db.cursor(buffered=True)
    cursor.execute(f"SELECT * FROM tbl_users WHERE id={user_id}")
    user = cursor.fetchone()

    if user:
        user_type = user[1]  
        
        if user_type == 'escort':
            cursor.execute(f"SELECT * FROM tbl_escort_info WHERE escort_id = {user_id}")
            existing_info = cursor.fetchone()

            if existing_info:
                cursor.execute(f"UPDATE tbl_escort_info SET gender='{gender}', bio='{bio}' WHERE user_id={user_id}")
            else:
                cursor.execute(f"INSERT INTO tbl_escort_info(escort_id, gender, bio) VALUES({user_id}, '{gender}', '{bio}')")

            g.db.commit()
            return jsonify({'success': 'Escort personal info updated successfully'})
        else:
            return jsonify({'error': 'Only escorts can update their personal info'}), 401
    else:
        return jsonify({'error': 'Invalid user ID'}), 404

#--------------------------------------------upload_document----------------------------------------


@authentication_bp.post('/upload_document/<user_id>')
def upload_document(user_id):
    cursor = g.db.cursor(buffered=True)
    cursor.execute(f"SELECT * FROM tbl_users WHERE id = {user_id} AND role = 'escort'")
    escort = cursor.fetchone()

    if escort:
        passport_image = request.files.get('passport_image')
        passport_front_image = request.files.get('passport_front_image')

        if passport_image:
            filename = secure_filename(passport_image.filename)
            passport_image.save(f"media/{filename}")
        if passport_front_image:
            filename = secure_filename(passport_front_image.filename)
            passport_front_image.save(f"media/{filename}")

        cursor.execute(f"UPDATE tbl_escort_info SET passport_image = '{passport_image.filename}', passport_front_image = '{passport_front_image.filename}' WHERE id = {user_id}")
        g.db.commit()
        return jsonify({'successful': 'User data added successfully'})
    return jsonify({'error': 'Only escorts can upload'}), 401

#--------------------------------------------set_body_preferences----------------------------------------


@authentication_bp.post('/set_body_preferences/<user_id>')
def set_body_preferences(user_id):
    data = request.json
    hair = data.get('hair')
    build = data.get('build')
    look=data.get('look')


    valid_hair = ['black', 'goldan', 'pink', 'red']
    valid_build = ['skinny', 'slim', 'fat']
    valid_look = ['sexy', 'ultasexy', 'prosexy']
    
    if hair not in valid_hair:
        return jsonify({'error': 'Invalid hair colour. Please provide a valid hair colour.'}), 400
    if build  not in valid_build:
        return jsonify({'error': 'Invalid build . Please provide a valid build.'}), 400
    if look not in valid_look:
        return jsonify({'error': 'Invalid look . Please provide a valid look.'}), 400

    cursor = g.db.cursor(buffered=True)
    cursor.execute(f"SELECT * FROM tbl_users WHERE id={user_id}")
    user = cursor.fetchone()

    if user:
        user_type = user[1]  
        
        if user_type == 'escort':
            cursor.execute(f"SELECT * FROM tbl_escort_info WHERE escort_id = {user_id}")
            existing_info = cursor.fetchone()

            if existing_info:
                cursor.execute(f"UPDATE tbl_escort_info SET hair='{hair}', build='{build}', look='{look}' WHERE escort_id={user_id}")
            else:
                cursor.execute(f"INSERT INTO tbl_escort_info(escort_id, hair,build,look) VALUES({user_id}, '{hair}', '{build}', '{look}')")

            g.db.commit()
            return jsonify({'success': 'Escort personal info updated successfully'})
        else:
            return jsonify({'error': 'Only escorts can update their personal info'}), 401
    else:
        return jsonify({'error': 'Invalid user ID'}), 404

#--------------------------------------------set_bank_info----------------------------------------


@authentication_bp.post('/set_bank_info/<user_id>')
def set_bank_info(user_id):
    data = request.json
    account_holder_name = data.get('account_holder_name')
    account_number = data.get('account_number')
    routing_number=data.get('routing_number')



    if not account_holder_name:
            return jsonify({'error':'please enter account_holder_name'}),400
    if not account_number:
        return jsonify({'error': 'please enter account_number'}), 400
    if not routing_number:
        return jsonify({'error': 'please enter routing_number'}), 400

    cursor = g.db.cursor(buffered=True)
    cursor.execute(f"SELECT * FROM tbl_users WHERE id={user_id}")
    user = cursor.fetchone()

    if user:
        user_type = user[1]  
        
        if user_type == 'escort':
            cursor.execute(f"SELECT * FROM tbl_escort_info WHERE escort_id = {user_id}")
            existing_info = cursor.fetchone()

            if existing_info:
                cursor.execute(f"UPDATE tbl_escort_info SET account_holder_name='{account_holder_name}', account_number='{account_number}', routing_number='{routing_number}' WHERE escort_id={user_id}")
            else:
                cursor.execute(f"INSERT INTO tbl_escort_info(escort_id, account_holder_name,account_number,routing_number) VALUES({user_id}, '{account_holder_name}', '{account_number}', '{routing_number}')")

            g.db.commit()
            return jsonify({'success': 'bank info updated successfully'})
        else:
            return jsonify({'error': 'Only escorts can update their personal info'}), 401
    else:
        return jsonify({'error': 'Invalid user ID'}), 404


#--------------------------------------------upload_image----------------------------------------


@authentication_bp.post('/upload_image/<user_id>')
def upload_image(user_id):
    cursor = g.db.cursor()
    cursor.execute(f"SELECT * FROM tbl_users WHERE id = {user_id} AND role = 'escort'")
    escort = cursor.fetchone()

    if escort:
        image = request.files.get('image')

        if image:
            filename = secure_filename(image.filename)
            image.save(f"media/{filename}")
        

        cursor.execute(f"UPDATE tbl_escort_image SET image = '{image.filename}' WHERE id = {user_id}")
        g.db.commit()
        return jsonify({'successful': 'User data added successfully'})
    return jsonify({'error': 'Only escorts can upload'}), 401


#--------------------------------------------upload_video----------------------------------------

@authentication_bp.post('/upload_video/<user_id>')
def upload_video(user_id):
    cursor = g.db.cursor()
    cursor.execute(f"SELECT * FROM tbl_users WHERE id = {user_id} AND role = 'escort'")
    escort = cursor.fetchone()

    if escort:
        video = request.files.get('video')
        data=request.form
        title=data.get('title')
        price=data.get('price')
        descripation=data.get('descripation')


        if video:
            filename = secure_filename(video.filename)
            video.save(f"media/{filename}")
        

        cursor.execute(f"UPDATE tbl_escort_video SET video = '{video.filename}',title='{title}',price='{price}',descripation='{descripation}' WHERE id = {user_id}")
        g.db.commit()
        return jsonify({'successful': 'User data added successfully'})
    return jsonify({'error': 'Only escorts can upload'}), 401

#--------------------------------------------update_profile----------------------------------------

@authentication_bp.post('/update_profile/<user_id>')
def update_profile(user_id):
    cursor = g.db.cursor()
    cursor.execute(f"SELECT * FROM tbl_users WHERE id={user_id}")
    user = cursor.fetchone()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.form
    profile_image = request.files.get('profile_image')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    username = data.get('username')
    phone = data.get('phone')
    email = data.get('email')

    if not first_name:
        return jsonify({'error': 'First name is required'}), 400

    if not last_name:
        return jsonify({'error': 'Last name is required'}), 400

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    if not phone:
        return jsonify({'error': 'Phone number is required'}), 400

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    if profile_image:
        filename = secure_filename(profile_image.filename)
        profile_image.save(f"media/{filename}")
        profile_image_filename = filename
    else:
        profile_image_filename = user['profile_image']

    cursor.execute(f"UPDATE tbl_users SET profile_image='{profile_image_filename}', first_name='{first_name}', last_name='{last_name}', username='{username}', phone='{phone}', email='{email}' WHERE id={user_id}")
    g.db.commit()

    return jsonify({'error': ''}), 200
