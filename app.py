import os
import uuid
import requests
import eventlet

eventlet.monkey_patch()

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from skimage.metrics import structural_similarity as ssim
from supabase import create_client
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import cv2
import numpy as np

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///campus_found_it.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(20), nullable=False)  # lost / found / returned
    user_id = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(500))
    matched = db.Column(db.Boolean, default=False)


# ---------- helpers ----------
def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


def require_admin():
    user = current_user()
    return user and user.is_admin


def ensure_admin_account():
    admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not admin:
        admin = User(
            name="Admin",
            email=ADMIN_EMAIL,
            password=generate_password_hash(ADMIN_PASSWORD),
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()


def upload_to_storage(image):
    if not image:
        return None, "Image required"

    file_bytes = image.read()
    filename = f"{uuid.uuid4()}_{secure_filename(image.filename)}"

    if supabase:
        try:
            supabase.storage.from_("item-images").upload(
                filename,
                file_bytes,
                {"content-type": image.content_type},
            )
            return {
                "filename": filename,
                "file_bytes": file_bytes,
                "public_url": supabase.storage.from_("item-images").get_public_url(filename),
            }, None
        except Exception as exc:
            return None, f"Supabase upload failed: {exc}"

    local_dir = os.path.join(app.static_folder, "uploads")
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, filename)
    with open(local_path, "wb") as f:
        f.write(file_bytes)
    return {
        "filename": filename,
        "file_bytes": file_bytes,
        "public_url": url_for("static", filename=f"uploads/{filename}", _external=True),
    }, None


def image_similarity(file_bytes, url):
    try:
        img1 = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
        response = requests.get(url, timeout=10)
        img2 = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)
        img1 = cv2.resize(img1, (300, 300))
        img2 = cv2.resize(img2, (300, 300))
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        score, _ = ssim(gray1, gray2, full=True)
        return score
    except Exception:
        return 0


# ---------- page routes ----------
@app.route("/")
def index():
    return render_template("index.html", user=current_user())


@app.route("/login-page")
def login_page():
    return render_template("login.html")


@app.route("/register-page")
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if not current_user():
        return redirect(url_for("login_page"))
    return render_template("dashboard.html", user=current_user())


@app.route("/admin/login")
def admin_login_page():
    return render_template("admin_login.html")


@app.route("/admin")
def admin_panel():
    if not require_admin():
        return redirect(url_for("admin_login_page"))

    items = Item.query.order_by(Item.id.desc()).all()
    users = User.query.order_by(User.id.desc()).all()
    stats = {
        "users": User.query.count(),
        "items": Item.query.count(),
        "lost": Item.query.filter_by(status="lost").count(),
        "found": Item.query.filter_by(status="found").count(),
        "matched": Item.query.filter_by(matched=True).count(),
    }
    return render_template("admin_dashboard.html", items=items, users=users, stats=stats, user=current_user())


# ---------- auth api ----------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    if not data.get("name") or not data.get("email") or not data.get("password"):
        return jsonify({"message": "Name, email and password are required"}), 400

    if User.query.filter_by(email=data["email"].strip().lower()).first():
        return jsonify({"message": "Email already exists"}), 400

    user = User(
        name=data["name"].strip(),
        email=data["email"].strip().lower(),
        password=generate_password_hash(data["password"]),
        is_admin=False,
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registered successfully"})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get("email", "").strip().lower()).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
    if not check_password_hash(user.password, data.get("password", "")):
        return jsonify({"message": "Wrong password"}), 401

    session["user_id"] = user.id
    return jsonify(
        {
            "message": "Login success",
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "redirect": "/admin" if user.is_admin else "/dashboard",
        }
    )


@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    user = User.query.filter_by(email=data.get("email", "").strip().lower(), is_admin=True).first()
    if not user or not check_password_hash(user.password, data.get("password", "")):
        return jsonify({"message": "Invalid admin credentials"}), 401

    session["user_id"] = user.id
    return jsonify({"message": "Admin login success", "redirect": "/admin"})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


# ---------- item api ----------
@app.route("/upload", methods=["POST"])
def upload():
    if not current_user():
        return jsonify({"message": "Login required"}), 401

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    status = request.form.get("status", "").strip().lower()
    image = request.files.get("image")

    if status not in {"lost", "found"}:
        return jsonify({"message": "Status must be lost or found"}), 400
    if not title:
        return jsonify({"message": "Title is required"}), 400

    uploaded, error = upload_to_storage(image)
    if error:
        return jsonify({"message": error}), 500

    new_item = Item(
        title=title,
        description=description,
        status=status,
        user_id=current_user().id,
        image_url=uploaded["public_url"],
    )
    db.session.add(new_item)
    db.session.commit()

    opposite = "found" if status == "lost" else "lost"
    candidates = Item.query.filter_by(status=opposite, matched=False).all()

    for item in candidates:
        if item.id == new_item.id:
            continue
        similarity = image_similarity(uploaded["file_bytes"], item.image_url)
        if similarity > 0.85:
            new_item.matched = True
            item.matched = True
            db.session.commit()
            socketio.emit(
                "match_found",
                {
                    "user1": new_item.user_id,
                    "user2": item.user_id,
                    "item1": new_item.title,
                    "item2": item.title,
                },
            )
            return jsonify({"message": "MATCH FOUND", "similarity": round(similarity * 100, 2)})

    return jsonify({"message": "Item uploaded"})


@app.route("/my-items/<int:user_id>")
def my_items(user_id):
    user = current_user()
    if not user:
        return jsonify({"message": "Login required"}), 401
    if user.id != user_id and not user.is_admin:
        return jsonify({"message": "Forbidden"}), 403

    items = Item.query.filter_by(user_id=user_id).order_by(Item.id.desc()).all()
    result = []
    for item in items:
        result.append(
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "status": item.status,
                "matched": item.matched,
                "image_url": item.image_url,
            }
        )
    return jsonify(result)


@app.route("/delete/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    user = current_user()
    if not user:
        return jsonify({"message": "Login required"}), 401

    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404
    if item.user_id != user.id and not user.is_admin:
        return jsonify({"message": "Forbidden"}), 403

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Deleted"})


# ---------- admin api ----------
@app.route("/admin/items")
def admin_items():
    if not require_admin():
        return jsonify({"message": "Admin required"}), 403
    data = []
    for item in Item.query.order_by(Item.id.desc()).all():
        owner = User.query.get(item.user_id)
        data.append(
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "status": item.status,
                "matched": item.matched,
                "image_url": item.image_url,
                "owner": owner.name if owner else "Unknown",
                "owner_email": owner.email if owner else "",
            }
        )
    return jsonify(data)


@app.route("/admin/items/<int:item_id>/status", methods=["PATCH"])
def admin_update_item_status(item_id):
    if not require_admin():
        return jsonify({"message": "Admin required"}), 403

    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404

    data = request.get_json() or {}
    new_status = data.get("status", "").strip().lower()
    if new_status not in {"lost", "found", "returned"}:
        return jsonify({"message": "Invalid status"}), 400

    item.status = new_status
    db.session.commit()
    return jsonify({"message": "Status updated"})


@app.route("/admin/items/<int:item_id>/toggle-match", methods=["PATCH"])
def admin_toggle_match(item_id):
    if not require_admin():
        return jsonify({"message": "Admin required"}), 403
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404
    item.matched = not item.matched
    db.session.commit()
    return jsonify({"message": "Match flag updated", "matched": item.matched})


@app.route("/admin/items/<int:item_id>", methods=["DELETE"])
def admin_delete_item(item_id):
    if not require_admin():
        return jsonify({"message": "Admin required"}), 403
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"message": "Item not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted"})


@app.route("/admin/users")
def admin_users():
    if not require_admin():
        return jsonify({"message": "Admin required"}), 403
    return jsonify(
        [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_admin": user.is_admin,
            }
            for user in User.query.order_by(User.id.desc()).all()
        ]
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_admin_account()
    port = int(os.environ.get("PORT", 10000))
    socketio.run(app, host="0.0.0.0", port=port)
