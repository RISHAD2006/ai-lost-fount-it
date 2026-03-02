# ======================================================
# 🔥 IMPORTANT FOR EVENTLET (MUST BE FIRST)
# ======================================================
import eventlet
eventlet.monkey_patch()

# ======================================================
# IMPORTS
# ======================================================
import os
import uuid
import cv2
import numpy as np
import requests

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from supabase import create_client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# ======================================================
# APP INIT
# ======================================================
app = Flask(__name__, template_folder="templates")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ======================================================
# ENV VARIABLES
# ======================================================
DATABASE_URL = os.environ.get("DATABASE_URL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
FROM_EMAIL = os.environ.get("FROM_EMAIL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL missing")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase credentials missing")

if not SENDGRID_API_KEY:
    raise Exception("SendGrid API key missing")

if not FROM_EMAIL:
    raise Exception("FROM_EMAIL missing")

# ======================================================
# DATABASE
# ======================================================
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ======================================================
# SUPABASE
# ======================================================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================================
# MODELS
# ======================================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(200))


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.String(500))
    status = db.Column(db.String(20))
    user_id = db.Column(db.Integer)
    image_url = db.Column(db.String(500))
    matched = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()

# ======================================================
# SENDGRID EMAIL
# ======================================================
def send_email(to_email, subject, content):
    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=f"<strong>{content}</strong>"
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        print("Email sent to", to_email)
    except Exception as e:
        print("SendGrid Error:", e)

# ======================================================
# ORB IMAGE MATCHING
# ======================================================
def orb_similarity(img1_bytes, img2_url):
    try:
        img1 = cv2.imdecode(np.frombuffer(img1_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)

        response = requests.get(img2_url, timeout=10)
        img2 = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_GRAYSCALE)

        if img1 is None or img2 is None:
            return 0

        orb = cv2.ORB_create(nfeatures=1500)

        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)

        if des1 is None or des2 is None:
            return 0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING)
        matches = bf.knnMatch(des1, des2, k=2)

        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append(m)

        return len(good)

    except Exception as e:
        print("ORB Error:", e)
        return 0

# ======================================================
# FRONTEND ROUTES
# ======================================================
@app.route("/")
def index_page():
    return render_template("index.html")

@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/register-page")
def register_page():
    return render_template("register.html")

@app.route("/dashboard-page")
def dashboard_page():
    return render_template("dashboard.html")

# ======================================================
# REGISTER
# ======================================================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid data"}), 400

    if User.query.filter_by(email=data.get("email")).first():
        return jsonify({"error": "Email already exists"}), 400

    user = User(
        name=data.get("name"),
        email=data.get("email"),
        password=generate_password_hash(data.get("password"))
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registered successfully"})

# ======================================================
# LOGIN
# ======================================================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    user = User.query.filter_by(email=data.get("email")).first()

    if not user or not check_password_hash(user.password, data.get("password")):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user_id": user.id,
        "name": user.name,
        "email": user.email
    })

# ======================================================
# UPLOAD + MATCH
# ======================================================
@app.route("/upload", methods=["POST"])
def upload():

    title = request.form.get("title")
    description = request.form.get("description")
    status = request.form.get("status")
    user_id = request.form.get("user_id")
    image = request.files.get("image")

    if not title or not description or not status or not user_id or not image:
        return jsonify({"error": "Missing fields"}), 400

    user_id = int(user_id)

    file_bytes = image.read()
    unique_name = str(uuid.uuid4()) + "_" + secure_filename(image.filename)

    # Upload to Supabase
    supabase.storage.from_("item-images").upload(
        path=unique_name,
        file=file_bytes,
        file_options={"content-type": image.content_type}
    )

    public_url = supabase.storage.from_("item-images").get_public_url(unique_name)

    new_item = Item(
        title=title,
        description=description,
        status=status,
        user_id=user_id,
        image_url=public_url,
        matched=False
    )

    db.session.add(new_item)
    db.session.commit()

    opposite = "found" if status == "lost" else "lost"
    candidates = Item.query.filter_by(status=opposite, matched=False).all()

    for item in candidates:
        if item.user_id == user_id:
            continue

        score = orb_similarity(file_bytes, item.image_url)

        if score > 40:
            new_item.matched = True
            item.matched = True
            db.session.commit()

            user1 = db.session.get(User, user_id)
            user2 = db.session.get(User, item.user_id)

            socketio.emit("match_found", {
                "user1": user1.id,
                "user2": user2.id
            })

            if user1 and user2:
                send_email(
                    user1.email,
                    "Match Found!",
                    f"Your item '{title}' matched. Contact: {user2.email}"
                )

                send_email(
                    user2.email,
                    "Match Found!",
                    f"Your item '{item.title}' matched. Contact: {user1.email}"
                )

            return jsonify({"message": "🔥 MATCH FOUND!"})

    return jsonify({"message": "Uploaded successfully"})

# ======================================================
# PUBLIC ROUTES
# ======================================================
@app.route("/all-lost")
def all_lost():
    items = Item.query.filter_by(status="lost").all()
    return jsonify([{
        "id": i.id,
        "title": i.title,
        "description": i.description,
        "image_url": i.image_url,
        "matched": i.matched
    } for i in items])

@app.route("/all-found")
def all_found():
    items = Item.query.filter_by(status="found").all()
    return jsonify([{
        "id": i.id,
        "title": i.title,
        "description": i.description,
        "image_url": i.image_url,
        "matched": i.matched
    } for i in items])

@app.route("/my-items/<int:user_id>")
def my_items(user_id):
    items = Item.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": i.id,
        "title": i.title,
        "status": i.status,
        "matched": i.matched,
        "image_url": i.image_url
    } for i in items])

# ======================================================
# RUN
# ======================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
