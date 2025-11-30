from flask import Flask, render_template, redirect, url_for

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def root():
        # default route -> login page
        return redirect(url_for("login"))

    @app.route("/login")
    def login():
        return render_template("auth/login.html")

    @app.route("/signup")
    def signup():
        return render_template("auth/signup.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    return app
