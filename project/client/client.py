from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required,get_jwt_identity,create_access_token
from werkzeug.utils import secure_filename




client_bp = Blueprint('client', __name__)

def is_client(user_id):
    cur = g.db.cursor()
    cur.execute(f"select role from tbl_users where id={user_id}")
    user = cur.fetchone()
    if user:
        if user[0] == 'client':
            return True
        return False
    
def is_client_escort(user_id):
    cur = g.db.cursor()
    cur.execute(f"select role from tbl_users where id={user_id}")
    user = cur.fetchone()
    if user:
        if user[0] == 'client' or user[0] == 'escort':
            return True
        return False


@client_bp.get('/access_token/<user_id>')
def access_token(user_id):
    access=create_access_token(identity=user_id)
    return jsonify({"token":access})

@client_bp.post("/verify_user_profile")
@jwt_required()
def verify_user_profile():
    user_id = get_jwt_identity()
    if not is_client_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    try:
        data = request.files
    except:
        return jsonify({"error":"no data found"}),404
    user_photo = data.get('user_photo')
    id_proof = data.get('id_proof')
    if not user_photo and not id_proof:
        return jsonify({"error":"no data found"}),404
    if not user_photo:
        return jsonify({"error":"user photo required"}),404
    if not id_proof:
        return jsonify({"error":"id_proof required"}),404
    user_photo_filename = secure_filename(user_photo.filename)
    id_proof_filename = secure_filename(id_proof.filename)
    user_id = get_jwt_identity()
    cur = g.db.cursor()
    cur.execute(f"insert into tbl_profile_verify (user_id,photo,id_proof) values ({user_id},'{user_photo_filename}','{id_proof_filename}')")
    g.db.commit()
    return jsonify({"message":"request send successfully"}),200

@client_bp.post("/like_feed/<feed_id>")
@jwt_required()
def like_feed(feed_id):
    user_id = get_jwt_identity()
    if not is_client_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor()
    cur.execute(f"insert into tbl_feed_like (user_id,feed_id) values ({user_id},{feed_id})")
    g.db.commit()
    return jsonify({"message":"liked successfully"}),200

@client_bp.delete("/dislike_feed/<feed_id>")
@jwt_required()
def dislike(feed_id):
    user_id = get_jwt_identity()
    if not is_client_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor()
    cur.execute(f"delete from tbl_feed_like where user_id={user_id} and feed_id={feed_id}")
    g.db.commit()
    return jsonify({"message":"disliked successfully"}),200

@client_bp.post("/add_comment/<feed_id>")
@jwt_required()
def add_comment(feed_id):
    user_id = get_jwt_identity()
    if not is_client_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    try:
        comment = request.json.get("comment")
    except:
        return jsonify({"error":"no data found"}),404
    if not comment:
        return jsonify({"error":"comment required"}),404
    cur = g.db.cursor()
    cur.execute(f"insert into tbl_feed_comment (user_id,feed_id,comment) values ({user_id},{feed_id},'{comment}')")
    g.db.commit()
    return jsonify({"message":"comment added successfully"}),200


@client_bp.get("/display_feed")
@jwt_required()
def display_feed():
    user_id = get_jwt_identity()
    if not is_client_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"select f.id,concat(u.first_name,' ',u.last_name) as escort_name, u.profile_image,f.caption,f.mood,f.location,f.like_count,f.comment_count,f.created_at from tbl_feed f join tbl_users u on f.escort_id = u.id order by f.created_at DESC")
    feed_data=cur.fetchall()
    cur.execute(f"select feed_id,media from tbl_feed_media")
    feed_media = cur.fetchall()
    
    for i in feed_data:
        media=[]
        for j in feed_media:
            if i['id'] == j['feed_id']:
                media.append(j['media'])
        i['media'] = media
    return jsonify({"feed_data":feed_data})

@client_bp.get("/display_comment/<feed_id>")
@jwt_required()
def display_comment(feed_id):
    user_id = get_jwt_identity()
    if not is_client_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"select concat(u.first_name,' ',u.last_name) as user_name,u.profile_image,fc.comment,fc.created_at from tbl_feed_comment fc join tbl_users u on fc.user_id = u.id where feed_id={feed_id} order by fc.created_at DESC")
    feed_comment_data = cur.fetchall()
    if not feed_comment_data:
        return jsonify({"error":"invalied feed id"}),400
    return jsonify({"feed_comment":feed_comment_data}),200
    
    
    
    


@client_bp.get("/user_profile")
@jwt_required()
def user_profile():
    user_id = get_jwt_identity()
    
    if not is_client(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"select first_name,last_name,username,profile_image,my_coins,is_profile_verify from tbl_users where id = {user_id}")
    data = cur.fetchone()
    return jsonify({"user_profile_data":data}),200


@client_bp.get("/purchased_videos")
@jwt_required()
def purchased_videos():
    user_id = get_jwt_identity()
    if not is_client(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"select ev.video,u.first_name,u.last_name from tbl_client_video_purchased_video vp join tbl_escort_video ev on vp.video_id=ev.id join tbl_users u on ev.escort_id=u.id where vp.client_id={user_id}")
    data = cur.fetchall()
    return jsonify({"purchased_videos":data}),200


@client_bp.get("/get_payments_detials")
@jwt_required()
def get_payments_detials():
    user_id = get_jwt_identity()
    if not is_client(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"select id,card_holder,card_number from tbl_user_payment_method where user_id={user_id} and is_active=1 and is_delete=0")
    data = cur.fetchall()
    return jsonify({"card_detials":data}),200


@client_bp.patch("/reomve_payment_method/<card_id>")
@jwt_required()
def reomve_payment_method(card_id):
    user_id = get_jwt_identity()
    if not is_client(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"select id from tbl_user_payment_method where user_id={user_id} and id={card_id}")
    card_data= cur.fetchone()
    if card_data:
        cur.execute(f"update tbl_user_payment_method set is_active=0,is_delete=1 where id={card_data['id']}")
        g.db.commit()
        return jsonify({"message":"card deleted successfully"}),200
    return jsonify({"error":"invalid card id"}),400

@client_bp.post("/add_payment_method")
@jwt_required()
def add_payment_method():
    user_id = get_jwt_identity()
    if not is_client(user_id):
        return jsonify({"error":"unauthrized access"}),401
    try:
        data = request.json
    except:
        return jsonify({"error":"no json data found"}),404
    card_holder = data.get("card_holder")
    card_number = data.get("card_number")
    exp_date = data.get("exp_date")
    cvv = data.get("cvv")
    if not card_holder or not card_number or not exp_date or not cvv:
        return jsonify({"error":"no data found"}),404
    if not card_number:
        return jsonify({"error":"card number required"}),404
    if not card_holder:
        return jsonify({"error":"card holder name required"}),404
    if not exp_date:
        return jsonify({"error":"exp date required"}),404
    if not cvv:
        return jsonify({"error":"cvv required"}),404
        
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"insert into tbl_user_payment_method (user_id,card_holder,card_number,expire_date,cvv) values ({user_id},'{card_holder}','{card_number}','{exp_date}',{cvv})")
    g.db.commit()
    return jsonify({"message":"payment method added successfully"}),200







#-------------------page.39------------------------------
@client_bp.get('/package')
@jwt_required()
def package():
    try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error": "unauthorized access"}), 401

        cursor = g.db.cursor(dictionary=True) 
        cursor.execute('SELECT price,name,descripation,fetures FROM tbl_package WHERE is_active=1 AND is_delete=0')
        user =cursor.fetchall()
        return jsonify({"Premium":user}),200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    

@client_bp.get('/package/<id>')
@jwt_required()
def package_single(id):
    try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error": "unauthorized access"}), 401
        
        cursor = g.db.cursor(dictionary=True)
        cursor.execute('SELECT price,name,descripation,fetures FROM tbl_package WHERE is_active=1 AND is_delete=0 AND id=%s', (id,))
        user =cursor.fetchall()

        if user:
           pass
        else:
            return jsonify({'error' : 'Not Found'}),400
        
        return jsonify({"Premium":user}),200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

    
#-----------------------------------------page.44---------------------------------------
#top_populer_img
@client_bp.get('/escort_image')
@jwt_required()
def escort_image():
    try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error":"unauthrized access"}),401
        
        cursor = g.db.cursor(dictionary=True)
        cursor.execute('SELECT tu.username,tei.image,tu.is_login FROM tbl_escort_image tei JOIN tbl_users tu ON tei.escort_id = tu.id WHERE tei.is_active=1 AND tei.like_count >= 50 AND tu.is_login=1')
        user =cursor.fetchall()
        return jsonify({"Top Populars":user}),200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#img
@client_bp.get('/escort_image_data')
@jwt_required()
def escort_image_data():
    try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error": "unauthorized access"}), 401
        
        cursor = g.db.cursor(dictionary=True)
        cursor.execute('SELECT tu.username,tei.image,tu.is_login FROM tbl_escort_image tei JOIN tbl_users tu ON tei.escort_id = tu.id WHERE tei.is_active=1 AND tei.like_count <= 50;')
        user =cursor.fetchall()
        return jsonify({"image":user}),200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#insert escort image 
@client_bp.post('/escort_image_insert')
@jwt_required()
def escort_image_insert():
    try:
        u_id=get_jwt_identity()

        escort_id = u_id

        cursor = g.db.cursor()

        cursor.execute(f"SELECT id FROM tbl_users WHERE role='escort' AND id='{escort_id}'")
        user =cursor.fetchall()
    
        print(user)

        if user:
           pass
        else:
            return jsonify({'error' : 'Escort are Insert the image'}),404
        
        image = request.json.get('image')

        if not image:
            return jsonify({'error': 'image is required'}), 400
      

        cursor = g.db.cursor()

        cursor.execute('INSERT INTO tbl_escort_image (escort_id,image) VALUES (%s, %s)',
                    (escort_id,image))
        
        g.db.commit() 
        return jsonify({'message' : 'Image are Insert'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#Page-45_Filter_by--------------------------------------------
#distance-------------
@client_bp.get('/filter_by')
@jwt_required()
def filter_by():
    try:
        u_id = get_jwt_identity()  
     
         
        if not is_client(u_id):
            return jsonify({"error":"unauthrized access"}),401
        
        print(u_id)
        id = u_id

        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id={id}")
        user_id = cursor.fetchone() 
        print(user_id)

        a = user_id['latitude']  
        print(a)
        b = user_id['longitude'] 
        print(b)

        start  = request.json.get('start_dis')
        end = request.json.get('end_dis')

        cursor.execute(f"""SELECT id,username, CONCAT(ROUND((6371 * ACOS(
                        COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                        SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                        ), 2), 'km') AS distance
                        FROM tbl_users tu
                        HAVING distance BETWEEN {start} AND {end}""")
        
        user = cursor.fetchall()

        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#------------------------age--page.45----------------------
@client_bp.get('/age')
@jwt_required()
def age():
    try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error":"unauthrized access"}),401
        
        start_age  = request.json.get('start_age')
        end_age = request.json.get('end_age')
        cursor = g.db.cursor(dictionary=True)

        cursor.execute(f"""SELECT id,username, CASE
                    WHEN MONTH(dob) < MONTH(CURDATE()) OR 
                    (MONTH(dob) = MONTH(CURDATE()) AND DAY(dob) <= DAY(CURDATE())) THEN
                    YEAR(CURDATE()) - YEAR(dob)
                ELSE
                    YEAR(CURDATE()) - YEAR(dob) - 1
                END AS Age
                FROM tbl_users
                HAVING Age BETWEEN {start_age} AND {end_age}""")
        user = cursor.fetchall()

        return jsonify(user), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ------------------------interest--page.45------------------------
@client_bp.get('/user_interest')
@jwt_required()
def user_interest():
    try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error":"unauthrized access"}),401
        
        interest = request.json.get('interest')

        cursor = g.db.cursor(dictionary=True)
        users = []

        for interest_item in interest:
            cursor.execute(
                'SELECT tui.interest, tu.username FROM tbl_user_interests tui JOIN tbl_users tu ON tui.user_id = tu.id WHERE tui.interest = %s',
                (interest_item,)
            )
            users += cursor.fetchall()

        return jsonify(users), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#-------------------gerder--page.45--------------------

@client_bp.get('/escort_gender')
@jwt_required()
def escort_gender():
    try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error":"unauthrized access"}),401
        
        gender  = request.json.get('gender')

        cursor = g.db.cursor(dictionary=True)
        cursor.execute('SELECT tu.username,tei.gender FROM tbl_escort_info tei JOIN tbl_users tu ON tei.escort_id = tu.id WHERE tei.gender =%s', (gender,))
        user = cursor.fetchall()

        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#-------------------------------escort_hair..page.45-----------------------
@client_bp.get('/escort_hair')
@jwt_required()
def escort_hair():
    try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error":"unauthrized access"}),401
        
        hair  = request.json.get('hair')

        cursor = g.db.cursor(dictionary=True)
        cursor.execute('SELECT tu.username,tei.hair FROM tbl_escort_info tei JOIN tbl_users tu ON tei.escort_id = tu.id WHERE tei.hair = %s' , (hair,))
        user = cursor.fetchall()

        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#---------------------------------escort_build--page.45----------------------------------
@client_bp.get('/escort_build')
@jwt_required()
def escort_build():
    try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error":"unauthrized access"}),401
        
        build  = request.json.get('build')

        cursor = g.db.cursor(dictionary=True)
        cursor.execute('SELECT tu.username,tei.build FROM tbl_escort_info tei JOIN tbl_users tu ON tei.escort_id = tu.id WHERE tei.build = %s' , (build,))
        user = cursor.fetchall()

        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#--------------------------------near_by____page.46------------------------

@client_bp.get('/near_by')
@jwt_required()
def near_by():
    try:
        u_id = get_jwt_identity() 
        if not is_client(u_id):
            return jsonify({"error":"unauthrized access"}),401
         
        print(u_id)

        id = u_id

        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id={id}")
        user_id = cursor.fetchone() 
        print(user_id)

        a = user_id['latitude']  
        print(a)
        b = user_id['longitude'] 
        print(b)

        cursor.execute(f"""SELECT tu.id,tu.is_login,tei.image, CONCAT(ROUND((6371 * ACOS(
                        COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                        SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                        ), 2), 'km') AS distance
                        FROM tbl_users tu JOIN tbl_escort_image tei ON tu.id = tei.escort_id
                        HAVING distance <= 5.5 """)
        
        user = cursor.fetchall()

        return jsonify(user), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#-------------------------------about_escort---page.47-------------------------------
@client_bp.get('/about_escort/<id>')
@jwt_required()
def about_escort(id):
    try:
        u_id=get_jwt_identity()
        

        c_id = u_id

        cursor = g.db.cursor()

        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id='{c_id}'")
        user = cursor.fetchone()

        if user:
            a = user[0]  
            b = user[1]  
            print(a)
            print(b)
        else:
            return jsonify({'error': 'Not Found'}), 404
        
        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"""SELECT tei.image, tu.is_login, tu.username, tu.address, tei.like_count, tel.look,tel.gender,tu.dob,tel.hair,tel.build,
                            CONCAT(ROUND((3956 * 2 * ACOS(
                            COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                             SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                            ), 2), 'miles') AS miles
                            FROM tbl_users tu
                            JOIN tbl_escort_image tei ON tu.id = tei.escort_id
                            JOIN tbl_escort_info tel ON tu.id = tel.escort_id
                            WHERE tu.id = {id} AND role='escort'
                            GROUP BY tei.escort_id""")
        
        user = cursor.fetchall()
        if user:
           pass
        else:
            return jsonify({'error': 'Escort Not Found'}), 404

        return jsonify({'about':user}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    




#-------------------------------client---page.50-------------------------------
@client_bp.get('/client_about/<id>')
@jwt_required()
def client_about(id):
    try:
        u_id=get_jwt_identity()
        
        cursor = g.db.cursor()

        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id='{u_id}'")

        user = cursor.fetchone()

        if user:
            a = user[0]  
            b = user[1]  
            print(a)
            print(b)
        else:
            return jsonify({'error': 'escort Not Found'}), 404
        
        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"""SELECT tei.image, tu.is_login, tu.username, tu.address, tei.like_count,tu.description,
                            CONCAT(ROUND((3956 * 2 * ACOS(
                            COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                             SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                            ), 2), 'miles') AS miles
                            FROM tbl_users tu
                            JOIN tbl_escort_image tei ON tu.id = tei.escort_id
                            WHERE tu.id = {id} AND role='client'
                            GROUP BY tei.escort_id""")
        
        user = cursor.fetchall()
        if user:
           pass
        else:
            return jsonify({'error': 'Client Not Found'}), 404


        return jsonify({'Profile':user}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
#--------------------------video_insert____page.54........................................

@client_bp.post('/video_insert')
@jwt_required()
def video_insert():
    try:
        u_id=get_jwt_identity()
        if not is_client(u_id):
            return jsonify({"error":"unauthrized access"}),401

        escort_id = u_id

        cursor = g.db.cursor()

        cursor.execute(f"SELECT * FROM tbl_users WHERE role='escort' AND id='{escort_id}'")

        user = cursor.fetchall()

        if user:
           pass
        else:
            return jsonify({'error': 'Escort Not Found'}), 404
        
        video = request.json.get('video')
        titel = request.json.get('titel')
        price = request.json.get('price')
        descripation = request.json.get('descripation')

        if not video:
            return jsonify({'error': 'video is required'}), 400
      
        
        if not titel:
            return jsonify({'error': 'titel is required'}), 400
        
        if not price:
            return jsonify({'error': 'price is required'}), 400
        
        if not descripation:
            return jsonify({'error': 'descripation is required'}), 400

       
        cursor.execute('INSERT INTO tbl_escort_video (escort_id,video,titel,price,descripation) VALUES (%s, %s, %s, %s, %s)',(escort_id,video,titel,price,descripation))
        g.db.commit() 
        return ({'message': 'Video Successfully Inserted'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#page..54---------------------------video_listing-----------------------------------------------
@client_bp.get('/video_listing')
@jwt_required()
def video_listing():
      try:
        user_id = get_jwt_identity()
        if not is_client(user_id):
            return jsonify({"error":"unauthrized access"}),401
        
        cursor = g.db.cursor(dictionary=True)
        cursor.execute('SELECT video,titel,price FROM tbl_escort_video')
        user = cursor.fetchall()
        return jsonify({'Video':user}), 200
      except Exception as e:
        return jsonify({'error': str(e)}), 500

#page..55/56-------------------------------video_click--------------------------------------
@client_bp.get('/video_click/<id>')
@jwt_required()
def video_click(id):
      try:
        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f'SELECT video,titel,price,descripation FROM tbl_escort_video WHERE id={id}')
        user = cursor.fetchall()
        return jsonify({'Video':user}), 200
      except Exception as e:
        return jsonify({'error': str(e)}), 500




#--------------------online_met............page.58-------------------------------------


@client_bp.post('/escort_online_met/<escort_id>')
@jwt_required()
def online_met(escort_id):
    try:
        id = get_jwt_identity()
        
        cursor = g.db.cursor()

        cursor.execute(f"SELECT * FROM tbl_users WHERE role='client' AND id = {id}")
        user = cursor.fetchone()
        print(user)
        if user:
            pass
        else:
            return jsonify({'error': 'client Not found'}),500

        cursor.execute(f"SELECT * FROM tbl_users WHERE role='escort' AND id={escort_id}")
        escort = cursor.fetchone()
        print(escort)
        if escort:
            pass
        else:
            return jsonify({'error': 'escort Not found'}),500

        met_type = request.json.get('met_type')
        met_date = request.json.get('met_date')
        met_time = request.json.get('met_time')
        

        if met_type not in ['online', 'offline']:
            return jsonify({"message": "met_type must be online or offline"}), 400
            
        if not met_date:
            return jsonify({'error': 'Date is required'}), 400
        
        if not met_time:
            return jsonify({'error': 'Time is required'}), 400
        

        cursor.execute('INSERT INTO tbl_escort_met (client_id,escort_id, met_type, met_date,met_time) VALUES (%s, %s, %s, %s, %s)',
                    (user[0], escort[0], met_type, met_date, met_time))
        g.db.commit()
        
        return {'message': 'Online Appointment Fix'}, 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500





#--------------------offline_met............page.58-------------------------------------


@client_bp.post('/escort_offline_met/<escort_id>')
@jwt_required()
def offline_met(escort_id):
    try:
        id = get_jwt_identity()
        cursor = g.db.cursor()

        cursor.execute(f"SELECT * FROM tbl_users WHERE role='client' AND id = {id}")
        user = cursor.fetchone()
        print(user)
        if user:
            pass
        else:
            return jsonify({'error': 'client Not found'}),500

        cursor.execute(f"SELECT * FROM tbl_users WHERE role='escort' AND id={escort_id}")
        escort = cursor.fetchone()
        print(escort)
        if escort:
            pass
        else:
            return jsonify({'error': 'escort Not found'}),500

        met_type = request.json.get('met_type')
        met_date = request.json.get('met_date')
        met_time = request.json.get('met_time')
        met_place = request.json.get('met_place')

        if met_type not in ['online', 'offline']:
            return jsonify({"message": "met_type must be online or offline"}), 400
            
        if not met_date:
            return jsonify({'error': 'Date is required'}), 400
        
        if not met_time:
            return jsonify({'error': 'Time is required'}), 400
        
        if not met_place:
            return jsonify({'error': 'place is required'}), 400



        cursor.execute('INSERT INTO tbl_escort_met (client_id,escort_id, met_type, met_date,met_time,met_place) VALUES (%s, %s, %s, %s, %s, %s)',
                    (user[0], escort[0], met_type, met_date, met_time,met_place))
        g.db.commit()
        
        return {'message': 'Online Appointment Fix'}, 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#-----------------------------------------MEET---------------------------------------------------------------
@client_bp.post('/escort_meet/<escort_id>')
@jwt_required()
def meet(escort_id):
    try:
        id = get_jwt_identity()
        cursor = g.db.cursor()

        cursor.execute(f"SELECT * FROM tbl_users WHERE role='client' AND id = {id}")
        user = cursor.fetchone()
        print(user)
        if user is None:
            return jsonify({'error': 'Client not found'}), 500

        cursor.execute(f"SELECT * FROM tbl_users WHERE role='escort' AND id={escort_id}")
        escort = cursor.fetchone()
        print(escort)
        if escort is None:
            return jsonify({'error': 'Escort not found'}), 500

        met_type = request.json.get('met_type')
        met_date = request.json.get('met_date')
        met_time = request.json.get('met_time')
        met_place = request.json.get('met_place')

        if met_type not in ['online', 'offline']:
            return jsonify({"message": "met_type must be online or offline"}), 400

        if not met_date:
            return jsonify({'error': 'Date is required'}), 400

        if not met_time:
            return jsonify({'error': 'Time is required'}), 400

        if met_type == 'offline' and not met_place:
            return jsonify({'error': 'Place is required for offline meetings'}), 400

        cursor.execute('INSERT INTO tbl_escort_met (client_id, escort_id, met_type, met_date, met_time, met_place) VALUES (%s, %s, %s, %s, %s, %s)',
                    (user[0], escort[0], met_type, met_date, met_time, met_place if met_type == 'offline' else None))
        g.db.commit()

        return {'message': 'Appointment Fixed'}, 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#-----------------------------------------rating_review___page.68-------------------------------------------------------
@client_bp.post('/escort_review_rating/<escort_id>')
@jwt_required()
def escort_review_rating(escort_id):
    try:
        id = get_jwt_identity()
        cursor = g.db.cursor()

        cursor.execute(f"SELECT * FROM tbl_users WHERE role='client' AND id = {id}")
        user = cursor.fetchone()
        print(user)
        if user is None:
            return jsonify({'error': 'Client not found'}), 500

        cursor.execute(f"SELECT * FROM tbl_users WHERE role='escort' AND id={escort_id}")
        escort = cursor.fetchone()
        print(escort)
        if escort is None:
            return jsonify({'error': 'Escort not found'}), 500

        rating = request.json.get('rating')
        review = request.json.get('review')
    
    
        if not rating and not review:
            return jsonify({'error': 'required'}), 400

        cursor.execute('INSERT INTO tbl_escort_rating_review (client_id, escort_id, rating, review) VALUES (%s, %s, %s, %s)',
                    (user[0], escort[0], rating, review))
        g.db.commit()

        return {'message': 'Successfully'}, 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#---------------review_rating_listing........page.68----------------------------------------

@client_bp.get('/review_rating_listing/<id>')
@jwt_required()
def review_rating_listing(id):
    try:

        cursor = g.db.cursor()

        cursor.execute(f'SELECT avg_rating,review_count FROM tbl_escort_info WHERE escort_id={id}')

        user = cursor.fetchone()
        print(user)

        if user is None:
            return jsonify({'error': 'Escort not found'}), 500

        review_data = {
            'avg_rating': user[0],
            'review_count': user[1]
        }

        return jsonify({'Review': review_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#---------------review_rating_comment........page.68----------------------------------------

@client_bp.get('/review_rating_comment/<id>')
@jwt_required()
def review_rating_comment(id):
    try:

        cursor = g.db.cursor(dictionary=True)

        cursor.execute(f'SELECT trr.client_id,tu.profile_image,tu.username,trr.rating,trr.review,trr.created_at FROM tbl_escort_rating_review trr JOIN tbl_users tu ON trr.client_id = tu.id WHERE escort_id={id}')
        
        comment = cursor.fetchall()
        
        if not comment:
            return jsonify({'error': 'Escort not found'}), 500
    
        return jsonify({ 'comment': comment}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#----------------------------coine----page.74-------------------
@client_bp.post('/coine')
def coins():
    try:
        cursor = g.db.cursor()

        coine = request.json.get('coine')
        price = request.json.get('price')

        cursor.execute('INSERT INTO tbl_coine (coine,price) VALUES (%s, %s)',
                        (coine,price))

        g.db.commit() 
        
        if not coine:
                return jsonify({'error': 'coine is required'}), 400
        
            
        if not price:
                return jsonify({'error': 'price is required'}), 400
            
    
        return jsonify({'message': 'Coins Successfully Insert'}), 20
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#----------------------coine_listing___page.74------------------------------
@client_bp.get('/coine_listing')
@jwt_required()
def coine_listing():
    try:

        cursor = g.db.cursor(dictionary=True)

        cursor.execute('SELECT coine,price FROM tbl_coine')

        coine = cursor.fetchall()
        return jsonify({ 'coine': coine}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#----------------------met_requests___.80------------------------------
from datetime import timedelta

@client_bp.get('/met_requests')
@jwt_required()
def met_requests():
    try:
        id = get_jwt_identity()
        if not is_client(id):
            return jsonify({"error":"unauthrized access"}),401
        
        cursor = g.db.cursor(dictionary=True)

        cursor.execute("""SELECT ei.image, tu.username, em.id, em.met_date,em.met_statuus, em.met_time, em.met_type
                        FROM tbl_escort_met em
                        JOIN tbl_escort_image ei ON em.escort_id = ei.escort_id
                        JOIN tbl_users tu ON em.escort_id = tu.id WHERE em.met_statuus='requested' GROUP BY em.id""")

        requests = cursor.fetchall()

        for request in requests:
            request['met_date'] = str(request['met_date'])
            request['met_time'] = str(request['met_time'])  

        return jsonify({'Requests': requests}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#------------------------------------------------met_request_online___page.81-----------------------------------------
@client_bp.get('/met_request_online/<id>')
@jwt_required()
def met_request_online(id):
    try:
        u_id = get_jwt_identity()  
        print(u_id)

        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id={u_id} AND role='client'")
        user_id = cursor.fetchone() 
        print(user_id)

        if not user_id:
            return jsonify({'error': 'client is required'}), 400


        a = user_id['latitude']  
        print(a)
        b = user_id['longitude'] 
        print(b)

        cursor = g.db.cursor(dictionary=True)

        cursor.execute(f"""SELECT ei.image, tu.username, em.id, em.met_date, em.met_time, em.met_type,tu.address,trr.rating,em.met_statuus,
                                CONCAT(ROUND((3956 * 2 * ACOS(
                                COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                                SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                                ), 2), 'miles') AS miles
                                FROM tbl_escort_met em
                                JOIN tbl_escort_image ei ON em.escort_id = ei.escort_id
                                JOIN tbl_users tu ON em.escort_id = tu.id
                                JOIN tbl_escort_rating_review trr ON em.escort_id = trr.escort_id
                                WHERE em.id={id} AND em.met_type = 'online' AND em.met_statuus='requested'""")
        
        request = cursor.fetchone()

        if request:
            request['met_date'] = str(request['met_date'])
            request['met_time'] = str(request['met_time'])
        else:
            return jsonify({'message': 'Online Request not found'}), 404

        return jsonify({'Online_Request_Details': request}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#------------------------------------------------met_request_offline___page.82-----------------------------------------

@client_bp.get('/met_request_offline/<id>')
@jwt_required()
def met_request_offline(id):
    try:
        u_id = get_jwt_identity()  
        print(u_id)

        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id={u_id} AND role='client'")
        user_id = cursor.fetchone() 
        print(user_id)

        if not user_id:
            return jsonify({'error': 'client is required'}), 400


        a = user_id['latitude']  
        print(a)
        b = user_id['longitude'] 
        print(b)

        cursor = g.db.cursor(dictionary=True)

        cursor.execute(f"""SELECT ei.image, tu.username, em.id, em.met_date, em.met_time, em.met_type,tu.address,trr.rating,em.met_statuus,
                                CONCAT(ROUND((3956 * 2 * ACOS(
                                COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                                SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                                ), 2), 'miles') AS miles
                                FROM tbl_escort_met em
                                JOIN tbl_escort_image ei ON em.escort_id = ei.escort_id
                                JOIN tbl_users tu ON em.escort_id = tu.id
                                JOIN tbl_escort_rating_review trr ON em.escort_id = trr.escort_id
                                WHERE em.id={id} AND em.met_type = 'offline' AND em.met_statuus='requested'""")
        
        request = cursor.fetchone()

        if request:
            request['met_date'] = str(request['met_date'])
            request['met_time'] = str(request['met_time'])
        else:
            return jsonify({'message': 'offline Request not found'}), 404

        return jsonify({'Offline_Request_Details': request}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#--------------------------------------met_upcoming------------------page.83------------------------------

from datetime import timedelta

@client_bp.get('/met_upcoming')
@jwt_required()
def met_upcoming():
    try:
        u_id = get_jwt_identity()  

        if not is_client(u_id):
            return jsonify({"error":"unauthrized access"}),401
        
        cursor = g.db.cursor(dictionary=True)

        cursor.execute("""SELECT ei.image, tu.username, em.id, em.met_date,em.met_statuus, em.met_time, em.met_type
                        FROM tbl_escort_met em
                        JOIN tbl_escort_image ei ON em.escort_id = ei.escort_id
                        JOIN tbl_users tu ON em.escort_id = tu.id WHERE em.met_statuus='accepted' GROUP BY em.id""")

        requests = cursor.fetchall()

        for request in requests:
            request['met_date'] = str(request['met_date'])
            request['met_time'] = str(request['met_time'])  

        return jsonify({'Upcoming': requests}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500




#------------------------------------------------met_upcoming_online___page.84-----------------------------------------
@client_bp.get('/met_upcoimg_online/<id>')
@jwt_required()
def met_upcoimg_online(id):
    try:
        u_id = get_jwt_identity()  
        print(u_id)

        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id={u_id} AND role='client'")
        user_id = cursor.fetchone() 
        print(user_id)

        if not user_id:
            return jsonify({'error': 'client is required'}), 400


        a = user_id['latitude']  
        print(a)
        b = user_id['longitude'] 
        print(b)

        cursor = g.db.cursor(dictionary=True)

        cursor.execute(f"""SELECT ei.image, tu.username, em.id, em.met_date, em.met_time, em.met_type,tu.address,trr.rating,em.met_statuus,
                                CONCAT(ROUND((3956 * 2 * ACOS(
                                COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                                SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                                ), 2), 'miles') AS miles
                                FROM tbl_escort_met em
                                JOIN tbl_escort_image ei ON em.escort_id = ei.escort_id
                                JOIN tbl_users tu ON em.escort_id = tu.id
                                JOIN tbl_escort_rating_review trr ON em.escort_id = trr.escort_id
                                WHERE em.id={id} AND em.met_type = 'online' AND em.met_statuus='accepted'""")
        
        request = cursor.fetchone()

        if request:
            request['met_date'] = str(request['met_date'])
            request['met_time'] = str(request['met_time'])
        else:
            return jsonify({'message': 'Upcomig Online request Not Found'}), 404

        return jsonify({'Online_Upcoming_Details': request}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#------------------------------------------------met_request_offline___page.85-----------------------------------------


@client_bp.get('/met_upcoimg_offline/<id>')
@jwt_required()
def met_upcoimg_offline(id):
    try:
        u_id = get_jwt_identity()  
        print(u_id)

        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id={u_id} AND role='client'")
        user_id = cursor.fetchone() 
        print(user_id)

        if not user_id:
            return jsonify({'error': 'client is required'}), 400


        a = user_id['latitude']  
        print(a)
        b = user_id['longitude'] 
        print(b)

        cursor = g.db.cursor(dictionary=True)

        cursor.execute(f"""SELECT ei.image, tu.username, em.id, em.met_date, em.met_time, em.met_type,tu.address,trr.rating,em.met_statuus,
                                CONCAT(ROUND((3956 * 2 * ACOS(
                                COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                                SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                                ), 2), 'miles') AS miles
                                FROM tbl_escort_met em
                                JOIN tbl_escort_image ei ON em.escort_id = ei.escort_id
                                JOIN tbl_users tu ON em.escort_id = tu.id
                                JOIN tbl_escort_rating_review trr ON em.escort_id = trr.escort_id
                                WHERE em.id={id} AND em.met_type = 'offline' AND em.met_statuus='accepted'""")
        
        request = cursor.fetchone()

        if request:
            request['met_date'] = str(request['met_date'])
            request['met_time'] = str(request['met_time'])
        else:
            return jsonify({'message': 'Upcomig offline request Not Found'}), 404

        return jsonify({'Offline_Upcoimg_Details': request}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500




#--------------------------------------met_past------------------page.86------------------------------

from datetime import timedelta

@client_bp.get('/met_past')
@jwt_required()
def met_past():
    try:
        u_id = get_jwt_identity() 
        
        if not is_client(u_id):
            return jsonify({"error":"unauthrized access"}),401
        
        cursor = g.db.cursor(dictionary=True)

        cursor.execute("""SELECT ei.image, tu.username, em.id, em.met_date,em.met_statuus, em.met_time, em.met_type
                        FROM tbl_escort_met em
                        JOIN tbl_escort_image ei ON em.escort_id = ei.escort_id
                        JOIN tbl_users tu ON em.escort_id = tu.id WHERE em.met_statuus='completed' GROUP BY em.id""")

        requests = cursor.fetchall()

        for request in requests:
            request['met_date'] = str(request['met_date'])
            request['met_time'] = str(request['met_time'])  

        return jsonify({'Upcoming': requests}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500




#------------------------------------------------met_past_online___page.87-----------------------------------------
@client_bp.get('/met_past_online/<id>')
@jwt_required()
def met_past_online(id):
    try:
        u_id = get_jwt_identity()  
        print(u_id)

        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id={u_id} AND role='client'")
        user_id = cursor.fetchone() 
        print(user_id)

        if not user_id:
            return jsonify({'error': 'client is required'}), 400


        a = user_id['latitude']  
        print(a)
        b = user_id['longitude'] 
        print(b)

        cursor = g.db.cursor(dictionary=True)

        cursor.execute(f"""SELECT ei.image, tu.username, em.id, em.met_date, em.met_time, em.met_type,tu.address,trr.rating,em.met_statuus,
                                CONCAT(ROUND((3956 * 2 * ACOS(
                                COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                                SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                                ), 2), 'miles') AS miles
                                FROM tbl_escort_met em
                                JOIN tbl_escort_image ei ON em.escort_id = ei.escort_id
                                JOIN tbl_users tu ON em.escort_id = tu.id
                                JOIN tbl_escort_rating_review trr ON em.escort_id = trr.escort_id
                                WHERE em.id={id} AND em.met_type = 'online' AND em.met_statuus='completed'""")
        
        request = cursor.fetchone()

        if request:
            request['met_date'] = str(request['met_date'])
            request['met_time'] = str(request['met_time'])
        else:
            return jsonify({'message': 'Past Online request Not Found'}), 404

        return jsonify({'Online_Past_Details': request}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



#------------------------------------------------met_past_offline___page.88-----------------------------------------


@client_bp.get('/met_past_offline/<id>')
@jwt_required()
def met_past_offline(id):
    try:
        u_id = get_jwt_identity()  
        print(u_id)

        cursor = g.db.cursor(dictionary=True)
        cursor.execute(f"SELECT latitude,longitude FROM tbl_users WHERE id={u_id} AND role='client'")
        user_id = cursor.fetchone() 
        print(user_id)

        if not user_id:
            return jsonify({'error': 'client is required'}), 400


        a = user_id['latitude']  
        print(a)
        b = user_id['longitude'] 
        print(b)

        cursor = g.db.cursor(dictionary=True)

        cursor.execute(f"""SELECT ei.image, tu.username, em.id, em.met_date, em.met_time, em.met_type,tu.address,trr.rating,em.met_statuus,
                                CONCAT(ROUND((3956 * 2 * ACOS(
                                COS(RADIANS({a})) * COS(RADIANS(tu.latitude)) * COS(RADIANS({b}) - RADIANS(tu.longitude)) +
                                SIN(RADIANS({a})) * SIN(RADIANS(tu.latitude)))
                                ), 2), 'miles') AS miles
                                FROM tbl_escort_met em
                                JOIN tbl_escort_image ei ON em.escort_id = ei.escort_id
                                JOIN tbl_users tu ON em.escort_id = tu.id
                                JOIN tbl_escort_rating_review trr ON em.escort_id = trr.escort_id
                                WHERE em.id={id} AND em.met_type = 'offline' AND em.met_statuus='completed'""")
        
        request = cursor.fetchone()

        if request:
            request['met_date'] = str(request['met_date'])
            request['met_time'] = str(request['met_time'])
        else:
            return jsonify({'message': 'Past offline request Not Found'}), 404

        return jsonify({'Offline_past_Details': request}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


