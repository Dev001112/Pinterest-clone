from flask import (
    Flask, render_template, redirect,
    url_for, request, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from sqlalchemy import or_
import os
import uuid

# global extensions
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # basic config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL",
        "sqlite:///app.db"  # for dev; can be changed to Postgres later
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # upload folder
    upload_folder = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message_category = "info"

    from .models import User, Pin, Message, Like, SavedPin

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------- AUTH ROUTES ----------

    @app.route("/")
    def root():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                flash("Logged in successfully.", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid email or password.", "danger")

        return render_template("auth/login.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username")
            email = request.form.get("email")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            if not username or not email or not password:
                flash("Please fill in all required fields.", "danger")
                return render_template("auth/signup.html")

            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("auth/signup.html")

            if User.query.filter_by(email=email).first():
                flash("Email already registered.", "danger")
                return render_template("auth/signup.html")

            if User.query.filter_by(username=username).first():
                flash("Username already taken.", "danger")
                return render_template("auth/signup.html")

            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash("Account created. You can now log in.", "success")
            return redirect(url_for("login"))

        return render_template("auth/signup.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    # ---------- DASHBOARD & PINS ----------

    @app.route("/dashboard")
    @login_required
    def dashboard():
        active_tab = request.args.get("tab", "home")

        chat_with_id = request.args.get("chat_with", type=int)
        share_pin_id = request.args.get("share_pin", type=int)

        pins = Pin.query.order_by(Pin.created_at.desc()).all()
        users = User.query.filter(User.id != current_user.id).all()

        chat_with_user = None
        conversation_messages = []
        if chat_with_id:
            chat_with_user = User.query.get(chat_with_id)
            if chat_with_user:
                conversation_messages = Message.query.filter(
                    or_(
                        (Message.sender_id == current_user.id) &
                        (Message.recipient_id == chat_with_id),
                        (Message.sender_id == chat_with_id) &
                        (Message.recipient_id == current_user.id),
                    )
                ).order_by(Message.created_at.asc()).all()

        contact_ids = set()
        all_my_msgs = Message.query.filter(
            or_(
                Message.sender_id == current_user.id,
                Message.recipient_id == current_user.id,
            )
        ).all()
        for m in all_my_msgs:
            other_id = m.recipient_id if m.sender_id == current_user.id else m.sender_id
            contact_ids.add(other_id)

        contacts = User.query.filter(User.id.in_(contact_ids)).all() if contact_ids else []

        share_pin = Pin.query.get(share_pin_id) if share_pin_id else None

        # liked/saved state
        user_liked_ids = {like.pin_id for like in current_user.likes}
        user_saved_ids = {save.pin_id for save in current_user.saves}

        return render_template(
            "dashboard.html",
            pins=pins,
            users=users,
            active_tab=active_tab,
            chat_with_user=chat_with_user,
            messages=conversation_messages,
            contacts=contacts,
            share_pin=share_pin,
            user_liked_ids=user_liked_ids,
            user_saved_ids=user_saved_ids,
        )

    @app.route("/upload", methods=["POST"])
    @login_required
    def upload_pin():
        title = request.form.get("title")
        description = request.form.get("description")
        tags = request.form.get("tags")
        image = request.files.get("image")

        if not title or not image:
            flash("Title and image are required.", "danger")
            return redirect(url_for("dashboard", tab="upload"))

        allowed_ext = {"jpg", "jpeg", "png", "gif"}
        if "." not in image.filename:
            flash("Invalid image file.", "danger")
            return redirect(url_for("dashboard", tab="upload"))

        ext = image.filename.rsplit(".", 1)[1].lower()
        if ext not in allowed_ext:
            flash("Only JPG, JPEG, PNG, GIF allowed.", "danger")
            return redirect(url_for("dashboard", tab="upload"))

        filename = f"{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(save_path)

        pin = Pin(
            title=title,
            description=description,
            image_filename=filename,
            author=current_user,
        )
        db.session.add(pin)
        db.session.commit()

        flash("Pin uploaded!", "success")
        return redirect(url_for("dashboard", tab="home"))

    # ---------- PROFILE (liked + saved pins) ----------

    @app.route("/profile")
    @login_required
    def profile():
        # pins the user liked (most recent like first)
        liked_pins = (
            Pin.query.join(Like, Like.pin_id == Pin.id)
            .filter(Like.user_id == current_user.id)
            .order_by(Like.created_at.desc())
            .all()
        )

        # pins the user saved (most recent save first)
        saved_pins = (
            Pin.query.join(SavedPin, SavedPin.pin_id == Pin.id)
            .filter(SavedPin.user_id == current_user.id)
            .order_by(SavedPin.created_at.desc())
            .all()
        )

        return render_template(
            "profile.html",
            liked_pins=liked_pins,
            saved_pins=saved_pins,
        )

    # ---------- LIKE / SAVE ----------

    @app.route("/pin/<int:pin_id>/like", methods=["POST"])
    @login_required
    def like_pin(pin_id):
        pin = Pin.query.get_or_404(pin_id)

        existing = Like.query.filter_by(
            user_id=current_user.id,
            pin_id=pin.id
        ).first()

        if existing:
            db.session.delete(existing)
            liked = False
        else:
            db.session.add(Like(user_id=current_user.id, pin_id=pin.id))
            liked = True

        db.session.commit()
        count = Like.query.filter_by(pin_id=pin.id).count()

        return jsonify({"ok": True, "liked": liked, "count": count})

    @app.route("/pin/<int:pin_id>/save", methods=["POST"])
    @login_required
    def save_pin(pin_id):
        pin = Pin.query.get_or_404(pin_id)

        existing = SavedPin.query.filter_by(
            user_id=current_user.id,
            pin_id=pin.id
        ).first()

        if existing:
            db.session.delete(existing)
            saved = False
        else:
            db.session.add(SavedPin(user_id=current_user.id, pin_id=pin.id))
            saved = True

        db.session.commit()

        return jsonify({"ok": True, "saved": saved})

    # ---------- MESSAGES ----------

    @app.route("/messages/send", methods=["POST"])
    @login_required
    def send_message():
        """Handles both:
        - normal DM form (redirects to messages tab)
        - AJAX pin-share (returns JSON, no redirect)
        """
        recipient_id_raw = request.form.get("recipient_id")
        text = request.form.get("text", "").strip()
        pin_id_raw = request.form.get("pin_id")

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if not recipient_id_raw:
            msg = "Please choose a user to message."
            if is_ajax:
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("dashboard", tab="messages"))

        try:
            recipient_id = int(recipient_id_raw)
        except ValueError:
            msg = "Invalid recipient."
            if is_ajax:
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("dashboard", tab="messages"))

        if recipient_id == current_user.id:
            msg = "You cannot message yourself."
            if is_ajax:
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("dashboard", tab="messages"))

        recipient = User.query.get(recipient_id)
        if not recipient:
            msg = "User not found."
            if is_ajax:
                return jsonify({"ok": False, "error": msg}), 404
            flash(msg, "danger")
            return redirect(url_for("dashboard", tab="messages"))

        pin = None
        if pin_id_raw:
            try:
                pin_id = int(pin_id_raw)
                pin = Pin.query.get(pin_id)
            except ValueError:
                pin = None

        if not text and not pin:
            msg = "Cannot send an empty message."
            if is_ajax:
                return jsonify({"ok": False, "error": msg}), 400
            flash(msg, "danger")
            return redirect(url_for("dashboard", tab="messages", chat_with=recipient_id))

        msg_obj = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            text=text if text else None,
            pin_id=pin.id if pin else None,
        )
        db.session.add(msg_obj)
        db.session.commit()

        if is_ajax:
            return jsonify({"ok": True})

        flash("Message sent.", "success")
        return redirect(url_for("dashboard", tab="messages", chat_with=recipient_id))

    # ---------- LIVE MESSAGES API ----------

    @app.route("/api/messages_for/<int:user_id>")
    @login_required
    def api_messages_for(user_id):
        other = User.query.get_or_404(user_id)

        msgs = Message.query.filter(
            or_(
                (Message.sender_id == current_user.id) &
                (Message.recipient_id == user_id),
                (Message.sender_id == user_id) &
                (Message.recipient_id == current_user.id),
            )
        ).order_by(Message.created_at.asc()).all()

        result = []
        for m in msgs:
            result.append({
                "id": m.id,
                "from_me": m.sender_id == current_user.id,
                "text": m.text,
                "created_at": m.created_at.isoformat(),
                "pin": {
                    "title": m.pin.title,
                    "description": m.pin.description,
                    "image_url": url_for(
                        "static",
                        filename="uploads/" + m.pin.image_filename
                    )
                } if m.pin else None
            })

        return jsonify({
            "other_username": other.username,
            "messages": result
        })

    # ---------- PINS API (live home feed) ----------

    @app.route("/api/pins")
    @login_required
    def api_pins():
        pins = Pin.query.order_by(Pin.created_at.desc()).all()

        user_liked_ids = {like.pin_id for like in current_user.likes}
        user_saved_ids = {save.pin_id for save in current_user.saves}

        items = []
        for p in pins:
            items.append({
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "author": p.author.username,
                "created_at": p.created_at.strftime("%Y-%m-%d"),
                "image_url": url_for("static", filename="uploads/" + p.image_filename),
                "likes_count": len(p.likes),
                "liked": p.id in user_liked_ids,
                "saved": p.id in user_saved_ids,
            })
        return jsonify({"pins": items})

    # ---------- USER SEARCH API ----------

    @app.route("/api/search_users")
    @login_required
    def search_users():
        q = request.args.get("q", "").strip()
        if not q:
            return jsonify({"results": []})

        users = User.query.filter(
            User.username.ilike(f"%{q}%")
        ).limit(10).all()

        return jsonify({
            "results": [
                {"id": u.id, "username": u.username}
                for u in users if u.id != current_user.id
            ]
        })

    return app
