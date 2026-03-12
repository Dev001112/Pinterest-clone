import sys, os, traceback
sys.path.insert(0, r'd:\pinterest')
os.chdir(r'd:\pinterest')

try:
    from app import create_app, db
    print(">> create_app OK")
    app = create_app()
    print(">> App built OK — routes registered")
    print(">> Starting on http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)
except Exception as e:
    print("\n\n=== STARTUP ERROR ===")
    traceback.print_exc()
    sys.exit(1)
