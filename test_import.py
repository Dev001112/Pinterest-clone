with open(r'd:\pinterest\test_log.txt', 'w') as f:
    f.write("step1: python started\n")

import sys
sys.path.insert(0, r'd:\pinterest')

with open(r'd:\pinterest\test_log.txt', 'a') as f:
    f.write("step2: os module works\n")

try:
    import flask
    with open(r'd:\pinterest\test_log.txt', 'a') as f:
        f.write(f"step3: flask imported, version={flask.__version__}\n")
except Exception as e:
    with open(r'd:\pinterest\test_log.txt', 'a') as f:
        f.write(f"step3 FAIL: {e}\n")

try:
    from app import create_app
    with open(r'd:\pinterest\test_log.txt', 'a') as f:
        f.write("step4: create_app imported\n")
except Exception as e:
    with open(r'd:\pinterest\test_log.txt', 'a') as f:
        import traceback, io
        buf = io.StringIO()
        traceback.print_exc(file=buf)
        f.write(f"step4 FAIL: {e}\n{buf.getvalue()}\n")
