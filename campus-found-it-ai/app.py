import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from flask_socketio import SocketIO
from skimage.metrics import structural_similarity as ssim
from supabase import create_client
import cv2
import os
import uuid
import numpy as np
import requests

app = Flask(__name__, template_folder="templates")
CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# =====================
# ENV VARIABLES
# =====================

DATABASE_URL = os.environ.get("DATABASE_URL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# =====================
# DATABASE
# =====================

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# =====================
# SUPABASE
# =====================

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# EMAIL
# =====================

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = EMAIL_USER
app.config["MAIL_PASSWORD"] = EMAIL_PASS
app.config["MAIL_DEFAULT_SENDER"] = EMAIL_USER

mail = Mail(app)

# =====================
# MODELS
# =====================

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
    image_filename = db.Column(db.String(500))
    matched = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()

# =====================
# FRONTEND ROUTES
# =====================

@app.route("/")
def home():
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


# =====================
# IMAGE SIMILARITY
# =====================

def calculate_image_similarity(file1_bytes, file2_url):

    try:

        nparr1 = np.frombuffer(file1_bytes, np.uint8)
        img1 = cv2.imdecode(nparr1, cv2.IMREAD_COLOR)

        response = requests.get(file2_url)

        nparr2 = np.frombuffer(response.content, np.uint8)
        img2 = cv2.imdecode(nparr2, cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            return 0

        img1 = cv2.resize(img1, (300,300))
        img2 = cv2.resize(img2, (300,300))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        score,_ = ssim(gray1,gray2,full=True)

        return score

    except Exception as e:
        print(e)
        return 0


# =====================
# REGISTER
# =====================

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message":"Email already exists"}),400

    user = User(
        name=data["name"],
        email=data["email"],
        password=generate_password_hash(data["password"])
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message":"Registered"})


# =====================
# LOGIN
# =====================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"message":"User not found"}),404

    if not check_password_hash(user.password,data["password"]):
        return jsonify({"message":"Wrong password"}),401

    return jsonify({
        "user_id":user.id,
        "name":user.name,
        "email":user.email
    })


# =====================
# UPLOAD ITEM
# =====================

@app.route("/upload", methods=["POST"])
def upload_item():

    title = request.form.get("title")
    description = request.form.get("description")
    status = request.form.get("status")
    user_id = int(request.form.get("user_id"))
    image = request.files.get("image")

    unique_name = str(uuid.uuid4())+"_"+secure_filename(image.filename)

    file_bytes = image.read()

    supabase.storage.from_("item-images").upload(
        unique_name,
        file_bytes,
        {"content-type": image.content_type}
    )

    public_url = supabase.storage.from_("item-images").get_public_url(unique_name)["publicUrl"]

    new_item = Item(
        title=title,
        description=description,
        status=status,
        user_id=user_id,
        image_filename=public_url
    )

    db.session.add(new_item)
    db.session.commit()

    opposite = "found" if status=="lost" else "lost"

    items = Item.query.filter_by(status=opposite, matched=False).all()

    for item in items:

        if item.user_id == user_id:
            continue

        similarity = calculate_image_similarity(file_bytes,item.image_filename)

        if similarity >= 0.6:

            new_item.matched=True
            item.matched=True
            db.session.commit()

            socketio.emit("match_found",{
                "user1":new_item.user_id,
                "user2":item.user_id
            })

            return jsonify({"message":"🔥 MATCH FOUND"})

    return jsonify({"message":"Item uploaded"})


# =====================
# MY ITEMS
# =====================

@app.route("/my-items/<int:user_id>")
def my_items(user_id):

    items = Item.query.filter_by(user_id=user_id).all()

    data=[]

    for i in items:

        data.append({
            "id":i.id,
            "title":i.title,
            "description":i.description,
            "status":i.status,
            "matched":i.matched,
            "image_url":i.image_filename
        })

    return jsonify(data)


# =====================
# DELETE
# =====================

@app.route("/delete/<int:item_id>",methods=["DELETE"])
def delete_item(item_id):

    item = db.session.get(Item,item_id)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message":"Deleted"})


# =====================
# RUN
# =====================

if __name__ == "__main__":

    port = int(os.environ.get("PORT",10000))

    socketio.run(app,host="0.0.0.0",port=port)
