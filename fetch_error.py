import urllib.request, json
try:
    req = urllib.request.urlopen("http://127.0.0.1:5000/dashboard")
    print("SUCCESS", req.status)
except urllib.error.HTTPError as e:
    with open(r'd:\pinterest\web_err.txt', 'w') as f:
        f.write(f"HTTP {e.code}: {e.reason}\n\n{e.read().decode('utf-8')}")
except Exception as e:
    with open(r'd:\pinterest\web_err.txt', 'w') as f:
        f.write(f"OTHER ERROR: {e}")
