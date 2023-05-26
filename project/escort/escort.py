from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

escort_bp = Blueprint('escort', __name__)

def is_escort(user_id):
    print(user_id)
    cur = g.db.cursor()
    cur.execute(f"select role from tbl_users where id={user_id}")
    user = cur.fetchone()
    if user:
        if user[0] == 'escort':
            return True
        return False

@escort_bp.post("/add_feed")
@jwt_required()
def add_feed():
    user_id = get_jwt_identity()
    if not is_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    try:
        data = request.form
        media = request.files.get("photos")
    except:
        return jsonify({"error":"no data found"}),404
    caption = data.get("caption")
    mood = data.get("mood")
    location = data.get("location")
    if not caption and not mood and not location and not media:
        return jsonify({"error":"no data found"}),404
    if not caption:
        return jsonify({"error":"caption required"}),404
    if not mood:
        return jsonify({"error":"mood required"}),404
    if not location:
        return jsonify({"error":"location required"}),404
    if not media:
        return jsonify({"error":"media required"}),404
    print(type(media.content_type))
    cur = g.db.cursor()
    cur.execute(f"insert into tbl_feed (escort_id,caption,mood,location) values ({user_id},'{caption}','{mood}','{location}')")
    g.db.commit()
    cur.execute(f"select id from tbl_feed where escort_id={user_id} order by id DESC LIMIT 1")
    feed_id = cur.fetchone()
    cur.execute(f"insert into tbl_feed_media (feed_id,media_type,media) values ({feed_id[0]},'{str(media.content_type)}','{media.filename}')")
    g.db.commit()
    return jsonify({"message":"feed added successfully"}),200
    
    
@escort_bp.get("/display_meet_request")
@jwt_required()
def meet_request():
    user_id = get_jwt_identity()
    if not is_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"select em.id as request_id,u.profile_image,concat(u.first_name,' ',u.last_name) as client_name, concat(em.met_date) as met_date,concat(em.met_time) as met_time,em.met_type from tbl_escort_met em join tbl_users u on em.client_id = u.id where em.escort_id={user_id} and em.met_statuus='requested'")
    data = cur.fetchall()
    return jsonify({"meeting_requests":data})

@escort_bp.get("/request_details/<request_id>")
@jwt_required()
def request_details(request_id):
    user_id = get_jwt_identity()
    if not is_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f'''SELECT (round((3961 * acos (cos (radians(u.latitude))* cos(radians(u2.latitude))* cos( radians(u.longitude) - radians(u2.longitude) )+ sin (radians(u.latitude) )* sin(radians(u2.latitude)))))) AS distance,em.id,concat(u.first_name,' ',u.last_name) as client_name,u.address,u.profile_image,concat(em.met_date) as met_date,concat(em.met_time) as met_time,em.met_type
                FROM tbl_escort_met em 
                join  tbl_users u on em.client_id=u.id 
                join tbl_users u2 on em.escort_id=u2.id 
                WHERE em.escort_id={user_id} and em.id={request_id}''')
    data = cur.fetchone()
    if data['met_type'] == "offline":
        cur.execute(f'''SELECT (round((3961 * acos (cos (radians(u.latitude))* cos(radians(u2.latitude))* cos( radians(u.longitude) - radians(u2.longitude) )+ sin (radians(u.latitude) )* sin(radians(u2.latitude)))))) AS distance,em.id,concat(u.first_name,' ',u.last_name) as client_name,u.address,u.profile_image,concat(em.met_date) as met_date,concat(em.met_time) as met_time,em.met_type,em.met_place
                FROM tbl_escort_met em 
                join  tbl_users u on em.client_id=u.id 
                join tbl_users u2 on em.escort_id=u2.id 
                WHERE em.escort_id={user_id} and em.id={request_id}''')
        data = cur.fetchone()
    return jsonify({"meeting_requests":data})


@escort_bp.put("/accept_met_request/<request_id>")
@jwt_required()
def accept_met_request(request_id):
    user_id = get_jwt_identity()
    if not is_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"update tbl_escort_met set met_statuus='accepted' where escort_id={user_id} and id={request_id}")
    g.db.commit()
    if cur.rowcount > 0:
        return jsonify({"message":"request accepted"}),200
    return jsonify({"error":"invalid request id"}),400

@escort_bp.get("/upcomming_meeting")
@jwt_required()
def upcomming_meeting():
    user_id = get_jwt_identity()
    if not is_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"select em.id as request_id,u.profile_image,concat(u.first_name,' ',u.last_name) as client_name, concat(em.met_date) as met_date,concat(em.met_time) as met_time,em.met_type from tbl_escort_met em join tbl_users u on em.client_id = u.id where em.escort_id={user_id} and em.met_statuus='accepted'")
    data = cur.fetchall()
    return jsonify({"upcomming_meeting":data})

@escort_bp.get("/past_meeting")
@jwt_required()
def past_meeting():
    user_id = get_jwt_identity()
    if not is_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"select em.id as request_id,u.profile_image,concat(u.first_name,' ',u.last_name) as client_name, concat(em.met_date) as met_date,concat(em.met_time) as met_time,em.met_type from tbl_escort_met em join tbl_users u on em.client_id = u.id where em.escort_id={user_id} and em.met_statuus='completed'")
    data = cur.fetchall()
    return jsonify({"past_meeting":data})


@escort_bp.post("/add_game_rules")
@jwt_required()
def add_game_rules():
    user_id = get_jwt_identity()
    if not is_escort(user_id):
        return jsonify({"error":"unauthrized access"}),401
    data = request.json
    rule1 = data.get("rule1")
    rule2 = data.get("rule2")
    rule3 = data.get("rule3")
    rule4 = data.get("rule4")
    rule5 = data.get("rule5")
    rule6 = data.get("rule6")
    per_roll_coin = data.get("per_roll_coin")
    if not rule1 and not rule2 and not rule3 and not rule4 and not rule5 and not rule6 and not per_roll_coin:
        return jsonify({"error":"no data found"}),404
    if not rule1:
        return jsonify({"rule1 is required"}),404
    if not rule2:
        return jsonify({"rule2 is required"}),404
    if not rule3:
        return jsonify({"rule3 is required"}),404
    if not rule4:
        return jsonify({"rule4 is required"}),404
    if not rule5:
        return jsonify({"rule5 is required"}),404
    if not rule6:
        return jsonify({"rule6 is required"}),404
    if not per_roll_coin:
        return jsonify({"per_roll_coin is required"}),404
    
    
    cur = g.db.cursor(dictionary=True)
    cur.execute(f"insert into tbl_game_rules (escort_id,rule1,rule2,rule3,rule4,rule5,rule6,per_roll_coin) values ({user_id},'{rule1}','{rule2}','{rule3}','{rule4}','{rule5}','{rule6}',{per_roll_coin})")
    g.db.commit()
    return jsonify({"message":"game rules set successfully"}),200