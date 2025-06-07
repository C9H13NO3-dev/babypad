# api.py
import ujson as json
import urequests as requests
import time

class BabyBuddyAPI:
    def __init__(self, secrets_path="secrets.json"):
        self.secrets = self.load_secrets(secrets_path)
        self.base_url = self.secrets["api"]["url"]
        self.token = self.secrets["api"]["token"]
        self.headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json"
        }
        self.children = []
        self.child_index = 0
        self.load_children()

    def load_secrets(self, path):
        with open(path) as f:
            return json.load(f)

    # --- Network Helpers ---

    def get(self, endpoint):
        url = self.base_url + endpoint + "/"
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"API GET {url} failed: {resp.status_code}")
        except Exception as e:
            print(f"API GET {url} error: {e}")
        return None

    def post(self, endpoint, data):
        url = self.base_url + endpoint + "/"
        try:
            resp = requests.post(url, headers=self.headers, data=json.dumps(data))
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                print(f"API POST {url} failed: {resp.status_code}")
        except Exception as e:
            print(f"API POST {url} error: {e}")
        return None

    # --- Children Management ---

    def load_children(self):
        resp = self.get("children")
        if resp and "results" in resp:
            self.children = resp["results"]
        else:
            self.children = []
        self.child_index = 0

    def active_child(self):
        if not self.children:
            return None
        return self.children[self.child_index]

    def child_initials(self):
        child = self.active_child()
        if not child:
            return "No Child"
        name = child.get("first_name", "") + " " + child.get("last_name", "")
        return "".join([n[0].upper() for n in name.split() if n])[:4]  # max 4 initials

    def next_child(self):
        if not self.children:
            return
        self.child_index = (self.child_index + 1) % len(self.children)

    def prev_child(self):
        if not self.children:
            return
        self.child_index = (self.child_index - 1) % len(self.children)

    # --- Activity Timers ---

    def get_active_timer(self, activity_name):
        resp = self.get("timers")
        if not resp or "results" not in resp:
            return None
        child = self.active_child()
        if not child:
            return None
        child_id = child["id"]
        for t in resp["results"]:
            if t["child"] == child_id and t["name"] == activity_name and t["end"] is None:
                return t
        return None

    def start_timer(self, activity_name, data=None):
        """Start a new timer for the active child."""
        child = self.active_child()
        if not child:
            print("No active child available for timer")
            return None
        payload = {
            "child": child["id"],
            "name": activity_name
        }
        if data:
            payload.update(data)
        return self.post("timers", payload)

    def stop_timer(self, timer_id, data=None):
        """Stop timer by posting to timer endpoint with end timestamp."""
        payload = data or {}
        return self.post(f"timers/{timer_id}/stop", payload)

    # --- Feeding Example ---

    def start_feeding(self):
        """Start a feeding timer."""
        timer = self.get_active_timer("feeding")
        if timer:
            return timer  # already running
        return self.start_timer("feeding", data={"type": "breast milk", "method": "both breasts"})

    def stop_feeding(self, timer_id, feed_type, method):
        """Stop feeding timer with details."""
        payload = {"type": feed_type, "method": method}
        return self.stop_timer(timer_id, payload)

    # --- Additional Logging Helpers ---

    def log_diaper_change(self, wet=True, solid=False):
        """Log a diaper change entry."""
        payload = {
            "child": self.active_child()["id"],
            "wet": 1 if wet else 0,
            "solid": 1 if solid else 0,
        }
        return self.post("changes", payload)

    def log_weight(self, weight):
        """Log a weight measurement (in grams)."""
        payload = {
            "child": self.active_child()["id"],
            "weight": weight,
        }
        return self.post("weight", payload)

    def log_temperature(self, temperature):
        """Log a temperature measurement in Celsius."""
        payload = {
            "child": self.active_child()["id"],
            "temperature": temperature,
        }
        return self.post("temperature", payload)

    # --- Status and Error Handling ---

    def is_connected(self):
        # Try simple GET to base url
        try:
            resp = requests.get(self.base_url)
            return resp.status_code == 200
        except:
            return False

