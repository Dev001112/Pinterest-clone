from flask import (
    Flask, render_template, redirect,
    url_for, request, flash
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
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
        "sqlite:///app.db"  # dev DB; later we can switch to PostgreSQL
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

    from .models import User, Pin

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------- ROUTES ----------

    @app.route("/")
    def root():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    # AUTH

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

    # DASHBOARD

    @app.route("/dashboard")
    @login_required
    def dashboard():
        # show all pins newest-first for now
        pins = Pin.query.order_by(Pin.created_at.desc()).all()
        return render_template("dashboard.html", pins=pins)

    # UPLOAD PIN

    @app.route("/upload", methods=["POST"])
    @login_required
    def upload_pin():
        title = request.form.get("title")
        description = request.form.get("description")
        tags = request.form.get("tags")  # not used yet, but kept

        image = request.files.get("image")

        if not title or not image:
            flash("Title and image are required.", "danger")
            return redirect(url_for("dashboard"))

        # basic extension check
        allowed_ext = {"jpg", "jpeg", "png", "gif"}
        if "." not in image.filename:
            flash("Invalid image file.", "danger")
            return redirect(url_for("dashboard"))

        ext = image.filename.rsplit(".", 1)[1].lower()
        if ext not in allowed_ext:
            flash("Only JPG, JPEG, PNG, GIF allowed.", "danger")
            return redirect(url_for("dashboard"))

        # generate unique filename
        filename = f"{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(save_path)

        # create pin
        pin = Pin(
            title=title,
            description=description,
            image_filename=filename,
            author=current_user
        )
        db.session.add(pin)
        db.session.commit()

        flash("Pin uploaded!", "success")
        return redirect(url_for("dashboard"))

    return app
