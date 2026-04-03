#!/usr/bin/env python3
"""
Run this on your VPS to add the /api/food endpoint to proxy.py:
  python3 /root/patch_food_proxy.py
"""
PROXY = "/root/mysite/proxy/proxy.py"

with open(PROXY, 'r') as f:
    c = f.read()

if '/api/food' in c:
    print("Already patched — skipping.")
    exit(0)

# ── 1. Add route to do_GET and do_POST dispatch ───────────────────────────────
# The proxy dispatches on path in do_GET/do_POST. Find the claude route and add food alongside it.
OLD_ROUTE = "elif path=='/api/claude':self.claude()"
NEW_ROUTE = "elif path=='/api/claude':self.claude()\n      elif path=='/api/food':self.food()"

if OLD_ROUTE not in c:
    # Try alternate spacing used in some versions
    OLD_ROUTE = "elif path == '/api/claude': self.handle_claude()"
    NEW_ROUTE  = "elif path == '/api/claude': self.handle_claude()\n            elif path == '/api/food': self.food()"

if OLD_ROUTE not in c:
    print("ERROR: Could not find claude route to anchor food route. Check proxy routing manually.")
    exit(1)

c = c.replace(OLD_ROUTE, NEW_ROUTE)
print("Route injected.")

# ── 2. Add food() method before the final HTTPServer line ─────────────────────
FOOD_METHOD = '''
  def food(self):
    import os as _os, json as _j
    if not self.auth(): return
    DATA_DIR = "/data/food"
    _os.makedirs(DATA_DIR, exist_ok=True)
    DATA_FILE = DATA_DIR + "/state.json"
    try:
      if self.command == "GET":
        if _os.path.exists(DATA_FILE):
          with open(DATA_FILE) as f:
            self.j(200, _j.load(f))
        else:
          self.j(200, {})
      elif self.command == "POST":
        body = _j.loads(self.body())
        with open(DATA_FILE, "w") as f:
          _j.dump(body, f)
        self.j(200, {"ok": True})
      else:
        self.j(405, {"error": "method not allowed"})
    except Exception as e:
      self.j(500, {"error": str(e)})

'''

OLD_TAIL = "HTTPServer(("
c = c.replace(OLD_TAIL, FOOD_METHOD + OLD_TAIL, 1)
print("food() method added.")

with open(PROXY, 'w') as f:
    f.write(c)

print("Done. Now rebuild the proxy:")
print("  cd /root/mysite && docker compose build --no-cache api-proxy && docker compose up -d api-proxy")
