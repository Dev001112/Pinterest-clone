"""
Debug script - run this to see the exact error:
  .venv\Scripts\python.exe debug_app.py
"""
import traceback, sys

try:
    from app import create_app, db
    app = create_app()
    print("✅ App created OK")

    with app.app_context():
        # Test all models import
        from app.models import User, Pin, Tag, Board, Like, SavedPin, Comment, Message, Notification, pin_tags
        print("✅ All models imported OK")

        # Test DB connection
        db.create_all()
        print("✅ db.create_all() OK")

        # Test routes import
        from app.routes.main import main
        from app.routes.auth import auth
        from app.routes.messages import messages
        from app.routes.api import api
        from app.routes.boards import boards_bp
        print("✅ All blueprints imported OK")

        # Test forms import
        from app.forms import LoginForm, SignupForm, PinForm, PinEditForm, CommentForm, BoardForm, EditProfileForm, SettingsForm
        print("✅ All forms imported OK")

    print("\n✅ Everything looks good! Run:  python run.py")

except Exception as e:
    print(f"\n❌ ERROR: {e}\n")
    traceback.print_exc()
    sys.exit(1)
