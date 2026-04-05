import os
import uuid
import re
import requests
import eventlet
eventlet.monkey_patch()

from flask import (
    Flask, request, jsonify,
    render_template, session, redirect, url_for
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
# APP SETUP
# ================================
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, supports_credentials=True)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "super-secret-change-this")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ================================
# ENV VARIABLES
# ================================
DATABASE_URL  = os.environ.get("DATABASE_URL", "")
SUPABASE_URL  = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY  = os.environ.get("SUPABASE_KEY", "")
ADMIN_EMAIL   = os.environ.get("ADMIN_EMAIL",   "admin@example.com")
ADMIN_PASSWORD= os.environ.get("ADMIN_PASSWORD","admin123")

if DATABASE_URL.startswith("postgres://"):
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
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone    = db.Column(db.String(20),  default="")   # NEW: contact number

class Item(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    status      = db.Column(db.String(20),  nullable=False)   # lost / found / returned
    user_id     = db.Column(db.Integer,     nullable=False)
    image_url   = db.Column(db.String(500))
    matched     = db.Column(db.Boolean,     default=False)
    contact     = db.Column(db.String(100), default="")       # NEW: uploader contact

# ================================
# HELPERS
# ================================
def is_admin():
    return session.get("is_admin", False) is True

def item_to_dict(i, include_contact=False):
    d = {
        "id":          i.id,
        "title":       i.title,
        "description": i.description or "",
        "status":      i.status,
        "user_id":     i.user_id,
        "image_url":   i.image_url or "",
        "matched":     i.matched,
        "contact":     i.contact or ""
    }
    return d

def user_to_dict(u):
    return {"id": u.id, "name": u.name, "email": u.email, "phone": u.phone or ""}

# ================================
# TEXT SIMILARITY (no heavy ML)
# ================================
def normalize(text):
    """Lowercase, remove special chars, extra spaces."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def keyword_score(text1, text2):
    """
    Count how many words from text1 appear in text2 and vice versa.
    Returns a score between 0 and 1.
    """
    words1 = set(normalize(text1).split())
    words2 = set(normalize(text2).split())

    # Remove very common short words
    stop = {"a", "an", "the", "is", "it", "in", "on", "at", "of", "and",
            "or", "my", "i", "was", "were", "have", "has", "with", "to"}
    words1 -= stop
    words2 -= stop

    if not words1 or not words2:
        return 0.0

    common = words1 & words2
    score = len(common) / max(len(words1), len(words2))
    return score

def char_similarity(a, b):
    """
    Simple character-level similarity (like fuzzy matching).
    Compares two strings character by character.
    """
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    matches = sum(ca == cb for ca, cb in zip(a, b))
    return matches / max(len(a), len(b))

def text_match_score(title1, desc1, title2, desc2):
    """
    Combine title + description similarity.
    Returns score 0-100.
    """
    t1 = (title1 or "") + " " + (desc1 or "")
    t2 = (title2 or "") + " " + (desc2 or "")

    kw  = keyword_score(t1, t2)          # keyword overlap
    ch  = char_similarity(t1, t2)         # character similarity

    # weighted average
    combined = (kw * 0.7) + (ch * 0.3)
    return round(combined * 100, 1)

# ================================
# IMAGE SIMILARITY (OpenCV + SSIM)
# ================================
def image_similarity(file_bytes, url):
    try:
        img1 = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
        resp = requests.get(url, timeout=10)
        img2 = cv2.imdecode(np.frombuffer(resp.content, np.uint8), cv2.IMREAD_COLOR)

        if img1 is None or img2 is None:
            return 0.0

        img1 = cv2.resize(img1, (300, 300))
        img2 = cv2.resize(img2, (300, 300))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        score, _ = ssim(gray1, gray2, full=True)
        return max(score, 0.0)
    except Exception:
        return 0.0

# ================================
# COMBINED MATCH SCORE
# ================================
def combined_score(file_bytes, new_item, candidate):
    img_score  = image_similarity(file_bytes, candidate.image_url) * 100   # 0-100
    text_score = text_match_score(
        new_item.title, new_item.description,
        candidate.title, candidate.description
    )
    # 60% image weight + 40% text weight
    final = (img_score * 0.6) + (text_score * 0.4)
    return round(final, 1)

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
    if is_admin():
        return redirect(url_for("admin_dashboard_page"))
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard_page():
    if not is_admin():
        return redirect(url_for("admin_login_page"))
    return render_template("admin_dashboard.html", admin_email=ADMIN_EMAIL)

@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    session.pop("admin_email", None)
    return redirect(url_for("admin_login_page"))

# ================================
# AUTH ROUTES
# ================================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name     = data.get("name",     "").strip()
    email    = data.get("email",    "").strip().lower()
    password = data.get("password", "")
    phone    = data.get("phone",    "").strip()

    if not name or not email or not password:
        return jsonify({"message": "All fields required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 400

    user = User(
        name=name, email=email, phone=phone,
        password=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registered successfully"})

@app.route("/login", methods=["POST"])
def login():
    data     = request.get_json() or {}
    email    = data.get("email",    "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    if not check_password_hash(user.password, password):
        return jsonify({"message": "Wrong password"}), 401

    return jsonify({
        "message": "Login success",
        "user_id": user.id,
        "name":    user.name,
        "email":   user.email,
        "phone":   user.phone or ""
    })

@app.route("/admin/login", methods=["POST"])
def admin_login():
    data     = request.get_json() or {}
    email    = data.get("email",    "").strip().lower()
    password = data.get("password", "")

    if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
        session["is_admin"]    = True
        session["admin_email"] = ADMIN_EMAIL
        return jsonify({"message": "Admin login success", "redirect": "/admin/dashboard"})

    return jsonify({"message": "Invalid admin credentials"}), 401

# ================================
# UPLOAD ITEM
# ================================
@app.route("/upload", methods=["POST"])
def upload():
    title       = request.form.get("title",       "").strip()
    description = request.form.get("description", "").strip()
    status      = request.form.get("status",      "").strip().lower()
    user_id     = request.form.get("user_id",     "")
    contact     = request.form.get("contact",     "").strip()   # NEW
    image       = request.files.get("image")

    if not title or not status or not user_id:
        return jsonify({"message": "Title, status and user_id required"}), 400
    if status not in ["lost", "found"]:
        return jsonify({"message": "Status must be lost or found"}), 400
    if not image:
        return jsonify({"message": "Image required"}), 400
    if supabase is None:
        return jsonify({"message": "Supabase not configured"}), 500

    # --- Upload image to Supabase Storage ---
    filename   = str(uuid.uuid4()) + "_" + secure_filename(image.filename)
    file_bytes = image.read()

    try:
        supabase.storage.from_("item-images").upload(
            filename, file_bytes, {"content-type": image.content_type}
        )
    except Exception as e:
        return jsonify({"message": "Image upload failed", "error": str(e)}), 500

    public_url = supabase.storage.from_("item-images").get_public_url(filename)

    # --- Save item to database ---
    new_item = Item(
        title=title, description=description,
        status=status, user_id=int(user_id),
        image_url=public_url, matched=False,
        contact=contact
    )
    db.session.add(new_item)
    db.session.commit()

    # --- Run matching against opposite items ---
    opposite   = "found" if status == "lost" else "lost"
    candidates = Item.query.filter_by(status=opposite, matched=False).all()

    best_match  = None
    best_score  = 0.0

    for candidate in candidates:
        if candidate.image_url:
            score = combined_score(file_bytes, new_item, candidate)
        else:
            score = text_match_score(
                new_item.title, new_item.description,
                candidate.title, candidate.description
            )

        if score > best_score:
            best_score = score
            best_match = candidate

    # Threshold: 40% score is enough for a match
    if best_match and best_score >= 40:
        new_item.matched = True
        best_match.matched = True
        db.session.commit()

        # Get contact info of the matching item owner
        match_user = User.query.get(best_match.user_id)
        contact_info = ""
        if match_user:
            contact_info = f"{match_user.name} | {match_user.email}"
            if match_user.phone:
                contact_info += f" | {match_user.phone}"

        socketio.emit("match_found", {
            "user1": new_item.user_id,
            "user2": best_match.user_id,
            "score": best_score,
            "matched_title": best_match.title,
            "contact": best_match.contact or contact_info
        })

        return jsonify({
            "message":       "MATCH FOUND! 🎉",
            "match_score":   best_score,
            "matched_item":  best_match.title,
            "contact":       best_match.contact or contact_info
        })

    return jsonify({"message": "Item uploaded. No match found yet.", "match_score": 0})

# ================================
# GET ALL ITEMS (public - all users can see)
# ================================
@app.route("/all-items", methods=["GET"])
def all_items():
    status_filter = request.args.get("status")  # optional filter: lost / found
    if status_filter:
        items = Item.query.filter_by(status=status_filter).order_by(Item.id.desc()).all()
    else:
        items = Item.query.order_by(Item.id.desc()).all()
    return jsonify([item_to_dict(i) for i in items])

# ================================
# GET MY ITEMS
# ================================
@app.route("/my-items/<int:user_id>", methods=["GET"])
def my_items(user_id):
    items = Item.query.filter_by(user_id=user_id).order_by(Item.id.desc()).all()
    return jsonify([item_to_dict(i) for i in items])

# ================================
# DELETE ITEM
# ================================
@app.route("/delete/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Deleted"})

# ================================
# TEXT MATCH SEARCH (frontend search bar)
# ================================
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    all_it = Item.query.all()
    results = []
    for it in all_it:
        score = text_match_score(query, "", it.title, it.description or "")
        if score >= 20:
            d = item_to_dict(it)
            d["score"] = score
            results.append(d)

    results.sort(key=lambda x: x["score"], reverse=True)
    return jsonify(results[:20])

# ================================
# ADMIN API
# ================================
@app.route("/admin/stats")
def admin_stats():
    if not is_admin():
        return jsonify({"message": "Unauthorized"}), 401
    return jsonify({
        "total_users":    User.query.count(),
        "total_items":    Item.query.count(),
        "lost_count":     Item.query.filter_by(status="lost").count(),
        "found_count":    Item.query.filter_by(status="found").count(),
        "returned_count": Item.query.filter_by(status="returned").count(),
        "matched_count":  Item.query.filter_by(matched=True).count()
    })

@app.route("/admin/users")
def admin_users():
    if not is_admin():
        return jsonify({"message": "Unauthorized"}), 401
    return jsonify([user_to_dict(u) for u in User.query.order_by(User.id.desc()).all()])

@app.route("/admin/items")
def admin_items():
    if not is_admin():
        return jsonify({"message": "Unauthorized"}), 401
    return jsonify([item_to_dict(i) for i in Item.query.order_by(Item.id.desc()).all()])

@app.route("/admin/item/<int:item_id>", methods=["PATCH"])
def admin_update_item(item_id):
    if not is_admin():
        return jsonify({"message": "Unauthorized"}), 401
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Not found"}), 404
    data = request.get_json() or {}
    if "status" in data:
        s = str(data["status"]).strip().lower()
        if s not in ["lost", "found", "returned"]:
            return jsonify({"message": "Invalid status"}), 400
        item.status = s
    if "matched" in data:
        item.matched = bool(data["matched"])
    db.session.commit()
    return jsonify({"message": "Updated", "item": item_to_dict(item)})

@app.route("/admin/item/<int:item_id>", methods=["DELETE"])
def admin_delete_item(item_id):
    if not is_admin():
        return jsonify({"message": "Unauthorized"}), 401
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Deleted"})

# ================================
# RUN
# ================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
