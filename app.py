import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
from skimage.metrics import structural_similarity as ssim
from supabase import create_client

import numpy as np
import cv2
import uuid
import os
import requests

# ================================
# APP
# ================================

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ================================
# ENV VARIABLES
# ================================

DATABASE_URL = os.environ.get("DATABASE_URL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ================================
# DATABASE
# ================================

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================================
# SUPABASE
# ================================

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================================
# MODELS
# ================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))


class Item(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    status = db.Column(db.String(20))
    user_id = db.Column(db.Integer)
    image_url = db.Column(db.String(500))
    matched = db.Column(db.Boolean, default=False)

# ================================
# PAGE ROUTES
# ================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login-page")
def login_page():
    return render_template("login.html")


@app.route("/register-page")
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ================================
# IMAGE MATCHING
# ================================

def image_similarity(file_bytes, url):

    try:

        img1 = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)

        response = requests.get(url)
        img2 = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)

        img1 = cv2.resize(img1, (300,300))
        img2 = cv2.resize(img2, (300,300))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        score,_ = ssim(gray1,gray2,full=True)

        return score

    except:
        return 0

# ================================
# REGISTER
# ================================

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:
        return jsonify({"message":"Invalid data"}),400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message":"Email already exists"}),400

    user = User(
        name=data["name"],
        email=data["email"],
        password=generate_password_hash(data["password"])
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message":"Registered successfully"})

# ================================
# LOGIN
# ================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"message":"User not found"}),404

    if not check_password_hash(user.password,data["password"]):
        return jsonify({"message":"Wrong password"}),401

    return jsonify({
        "message":"Login success",
        "user_id":user.id,
        "name":user.name,
        "email":user.email
    })

# ================================
# UPLOAD ITEM
# ================================

@app.route("/upload", methods=["POST"])
def upload():

    title = request.form.get("title")
    description = request.form.get("description")
    status = request.form.get("status")
    user_id = request.form.get("user_id")
    image = request.files.get("image")

    if not image:
        return jsonify({"message":"Image required"}),400

    filename = str(uuid.uuid4()) + "_" + secure_filename(image.filename)

    file_bytes = image.read()

    try:

        supabase.storage.from_("item-images").upload(
            filename,
            file_bytes,
            {"content-type":image.content_type}
        )

    except Exception as e:

        return jsonify({"message":"Upload failed","error":str(e)}),500

    public_url = supabase.storage.from_("item-images").get_public_url(filename)

    new_item = Item(
        title=title,
        description=description,
        status=status,
        user_id=user_id,
        image_url=public_url
    )

    db.session.add(new_item)
    db.session.commit()

    # ================================
    # AI MATCH
    # ================================

    opposite = "found" if status=="lost" else "lost"

    candidates = Item.query.filter_by(status=opposite,matched=False).all()

    for item in candidates:

        similarity = image_similarity(file_bytes,item.image_url)

        if similarity > 0.85:

            new_item.matched=True
            item.matched=True

            db.session.commit()

            socketio.emit("match_found",{
                "user1":new_item.user_id,
                "user2":item.user_id
            })

            return jsonify({
                "message":"🔥 MATCH FOUND",
                "similarity":round(similarity*100,2)
            })

    return jsonify({"message":"Item uploaded"})

# ================================
# GET ITEMS
# ================================

@app.route("/my-items/<int:user_id>")
def my_items(user_id):

    items = Item.query.filter_by(user_id=user_id).all()

    result=[]

    for i in items:

        result.append({
            "id":i.id,
            "title":i.title,
            "description":i.description,
            "status":i.status,
            "matched":i.matched,
            "image_url":i.image_url
        })

    return jsonify(result)

# ================================
# DELETE
# ================================

@app.route("/delete/<int:id>",methods=["DELETE"])
def delete(id):

    item = Item.query.get(id)

    if not item:
        return jsonify({"message":"Item not found"}),404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message":"Deleted"})

# ================================
# RUN SERVER
# ================================

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT",10000))

    socketio.run(app, host="0.0.0.0", port=port)
