import subprocess, sys

def check_file(filename):
    try:
        subprocess.check_output([sys.executable, "-m", "py_compile", filename], stderr=subprocess.STDOUT)
        return ""
    except subprocess.CalledProcessError as e:
        return f"{filename} syntax error:\n{e.output.decode('utf-8')}\n"

errors = ""
errors += check_file(r"d:\pinterest\app\__init__.py")
errors += check_file(r"d:\pinterest\app\routes\main.py")
errors += check_file(r"d:\pinterest\app\routes\auth.py")
errors += check_file(r"d:\pinterest\app\routes\messages.py")
errors += check_file(r"d:\pinterest\app\routes\api.py")
errors += check_file(r"d:\pinterest\app\models.py")

with open(r"d:\pinterest\py_syntax.txt", "w") as f:
    f.write(errors if errors else "NO SYNTAX ERRORS")

print("Done")
