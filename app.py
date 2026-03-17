import os
import uuid
import requests
import eventlet
eventlet.monkey_patch()

from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for
)
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from skimage.metrics import structural_similarity as ssim
from supabase import create_client
import numpy as np
import cv2

# ================================
# APP
# ================================
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, supports_credentials=True)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "super-secret-change-this")

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ================================
# ENV VARIABLES
# ================================
DATABASE_URL = os.environ.get("DATABASE_URL")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///foundit.db"

# ================================
# DATABASE
# ================================
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ================================
# SUPABASE
# ================================
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================================
# MODELS
# ================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(20), nullable=False)   # lost / found / returned
    user_id = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500))
    matched = db.Column(db.Boolean, default=False)

# ================================
# HELPERS
# ================================
def is_admin_logged_in():
    return session.get("is_admin", False) is True

def admin_required():
    if not is_admin_logged_in():
        return False
    return True

def item_to_dict(i):
    return {
        "id": i.id,
        "title": i.title,
        "description": i.description,
        "status": i.status,
        "user_id": i.user_id,
        "image_url": i.image_url,
        "matched": i.matched
    }

def user_to_dict(u):
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email
    }

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
# ADMIN PAGE ROUTES
# ================================
@app.route("/admin/login-page")
def admin_login_page():
    if is_admin_logged_in():
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not is_admin_logged_in():
        return redirect(url_for("admin_login_page"))
    return render_template("admin_dashboard.html", admin_email=ADMIN_EMAIL)

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    session.pop("admin_email", None)
    return redirect(url_for("admin_login_page"))

# ================================
# IMAGE MATCHING
# ================================
def image_similarity(file_bytes, url):
    try:
        img1 = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)

        response = requests.get(url, timeout=10)
        img2 = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            return 0

        img1 = cv2.resize(img1, (300, 300))
        img2 = cv2.resize(img2, (300, 300))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        score, _ = ssim(gray1, gray2, full=True)
        return score
    except Exception:
        return 0

# ================================
# REGISTER
# ================================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Invalid data"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400

    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registered successfully"})

# ================================
# LOGIN
# ================================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user.password, password):
        return jsonify({"message": "Wrong password"}), 401

    return jsonify({
        "message": "Login success",
        "user_id": user.id,
        "name": user.name,
        "email": user.email
    })

# ================================
# ADMIN LOGIN
# ================================
@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json()

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
        session["is_admin"] = True
        session["admin_email"] = ADMIN_EMAIL
        return jsonify({
            "message": "Admin login success",
            "redirect": "/admin/dashboard"
        })

    return jsonify({"message": "Invalid admin credentials"}), 401

# ================================
# UPLOAD ITEM
# ================================
@app.route("/upload", methods=["POST"])
def upload():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    status = request.form.get("status", "").strip().lower()
    user_id = request.form.get("user_id")
    image = request.files.get("image")

    if not title or not status or not user_id:
        return jsonify({"message": "Title, status and user_id are required"}), 400

    if status not in ["lost", "found"]:
        return jsonify({"message": "Status must be 'lost' or 'found'"}), 400

    if not image:
        return jsonify({"message": "Image required"}), 400

    if supabase is None:
        return jsonify({"message": "Supabase is not configured"}), 500

    filename = str(uuid.uuid4()) + "_" + secure_filename(image.filename)
    file_bytes = image.read()

    try:
        supabase.storage.from_("item-images").upload(
            filename,
            file_bytes,
            {"content-type": image.content_type}
        )
    except Exception as e:
        return jsonify({"message": "Upload failed", "error": str(e)}), 500

    public_url = supabase.storage.from_("item-images").get_public_url(filename)

    new_item = Item(
        title=title,
        description=description,
        status=status,
        user_id=int(user_id),
        image_url=public_url,
        matched=False
    )

    db.session.add(new_item)
    db.session.commit()

    opposite = "found" if status == "lost" else "lost"
    candidates = Item.query.filter_by(status=opposite, matched=False).all()

    for item in candidates:
        similarity = image_similarity(file_bytes, item.image_url)
        if similarity > 0.85:
            new_item.matched = True
            item.matched = True
            db.session.commit()

            socketio.emit("match_found", {
                "user1": new_item.user_id,
                "user2": item.user_id
            })

            return jsonify({
                "message": "MATCH FOUND",
                "similarity": round(similarity * 100, 2)
            })

    return jsonify({"message": "Item uploaded"})

# ================================
# USER ITEMS
# ================================
@app.route("/my-items/<int:user_id>", methods=["GET"])
def my_items(user_id):
    items = Item.query.filter_by(user_id=user_id).order_by(Item.id.desc()).all()
    return jsonify([item_to_dict(i) for i in items])

# ================================
# DELETE ITEM (USER/GENERAL)
# ================================
@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_item(id):
    item = Item.query.get(id)
    if not item:
        return jsonify({"message": "Item not found"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Deleted"})

# ================================
# ADMIN API
# ================================
@app.route("/admin/stats", methods=["GET"])
def admin_stats():
    if not admin_required():
        return jsonify({"message": "Unauthorized"}), 401

    total_users = User.query.count()
    total_items = Item.query.count()
    lost_count = Item.query.filter_by(status="lost").count()
    found_count = Item.query.filter_by(status="found").count()
    returned_count = Item.query.filter_by(status="returned").count()
    matched_count = Item.query.filter_by(matched=True).count()

    return jsonify({
        "total_users": total_users,
        "total_items": total_items,
        "lost_count": lost_count,
        "found_count": found_count,
        "returned_count": returned_count,
        "matched_count": matched_count
    })

@app.route("/admin/users", methods=["GET"])
def admin_users():
    if not admin_required():
        return jsonify({"message": "Unauthorized"}), 401

    users = User.query.order_by(User.id.desc()).all()
    return jsonify([user_to_dict(u) for u in users])

@app.route("/admin/items", methods=["GET"])
def admin_items():
    if not admin_required():
        return jsonify({"message": "Unauthorized"}), 401

    items = Item.query.order_by(Item.id.desc()).all()
    return jsonify([item_to_dict(i) for i in items])

@app.route("/admin/item/<int:item_id>", methods=["PATCH"])
def admin_update_item(item_id):
    if not admin_required():
        return jsonify({"message": "Unauthorized"}), 401

    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404

    data = request.get_json() or {}

    new_status = data.get("status")
    matched = data.get("matched")

    if new_status is not None:
        new_status = str(new_status).strip().lower()
        if new_status not in ["lost", "found", "returned"]:
            return jsonify({"message": "Invalid status"}), 400
        item.status = new_status

    if matched is not None:
        item.matched = bool(matched)

    db.session.commit()

    return jsonify({
        "message": "Item updated successfully",
        "item": item_to_dict(item)
    })

@app.route("/admin/item/<int:item_id>", methods=["DELETE"])
def admin_delete_item(item_id):
    if not admin_required():
        return jsonify({"message": "Unauthorized"}), 401

    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404

    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Item deleted successfully"})

# ================================
# RUN SERVER
# ================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
