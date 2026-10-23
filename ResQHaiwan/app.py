"""ResQHaiwan prototype backend.
Run:  pip install -r requirements.txt
      uvicorn app:app --reload --host 0.0.0.0
Open: http://localhost:8000
"""
from pathlib import Path
import base64, hashlib, io, math, secrets, time, uuid
from collections import defaultdict
import numpy as np
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel
from ultralytics import YOLO

BASE = Path(__file__).resolve().parent
app = FastAPI(title="ResQHaiwan")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
model = YOLO("yolov8n.pt")  # pretrained on COCO; class 16 = dog (downloads on first run)
REPORTS: dict[str, dict] = {}  # in-memory for the prototype; swap for PostgreSQL/PostGIS later

SEVERITY = {"attack": 5, "chasing": 4, "pack": 3, "aggressive": 3, "injured": 2, "sighting": 1}
ACTIVE_HOURS = 6        # reports fade from the map after this
NEARBY_M = 300          # reports within this radius count as corroboration

# DRAFT wording - have MPSPK / Veterinary Services / MOH review before real use.
GUIDANCE = {
    "chasing": ["Stay calm and stop running. Running encourages a chase.",
                "Stand still, side-on to the dog, arms close. Avoid staring at it.",
                "Back away slowly. Put a bag or object between you and the dog.",
                "Get behind a gate, car or shop door, then tap \"I'm safe now\"."],
    "bitten": ["Move away from the dog to a safe place.",
               "Wash the wound with soap and running water for at least 15 minutes.",
               "Go to the nearest clinic or hospital today for rabies and tetanus assessment.",
               "Report the location so others nearby are warned."],
    "nearby": ["Do not approach, feed or stare at the dog.",
               "Keep your distance and walk away calmly. Keep children close.",
               "Take photos only from a safe distance."],
    "safe": ["Take a photo of the area from a safe distance if you can.",
             "Submit the report. People nearby will be alerted once it is verified."],
}


GUIDANCE_MS = {
    "chasing": ["Bertenang dan berhenti berlari. Berlari menggalakkan anjing mengejar.",
                "Berdiri menyisi, rapatkan tangan. Jangan renung anjing itu.",
                "Berundur perlahan-lahan. Letakkan beg atau objek di antara anda dan anjing.",
                "Masuk ke belakang pagar, kereta atau kedai, kemudian tekan \"Saya sudah selamat\"."],
    "bitten": ["Menjauhi anjing ke tempat yang selamat.",
               "Basuh luka dengan sabun dan air mengalir sekurang-kurangnya 15 minit.",
               "Pergi ke klinik atau hospital berdekatan hari ini untuk penilaian rabies dan tetanus.",
               "Laporkan lokasi supaya orang sekitar diberi amaran."],
    "nearby": ["Jangan dekati, beri makan atau renung anjing itu.",
               "Jaga jarak dan berjalan pergi dengan tenang. Pastikan kanak-kanak dekat dengan anda.",
               "Ambil gambar dari jarak yang selamat sahaja."],
    "safe": ["Ambil gambar kawasan dari jarak selamat jika boleh.",
             "Hantar laporan. Orang sekitar akan dimaklumkan selepas ia disahkan."],
}


def dist_m(a_lat, a_lng, b_lat, b_lng):
    r = math.radians
    h = math.sin(r(b_lat - a_lat) / 2) ** 2 + math.cos(r(a_lat)) * math.cos(r(b_lat)) * math.sin(r(b_lng - a_lng) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def analyse(img: Image.Image):
    """Return (dog confidences, is_sharp)."""
    res = model(img, classes=[16], conf=0.25, verbose=False)[0]
    dogs = [float(c) for c in res.boxes.conf]
    g = np.asarray(img.convert("L").resize((320, 240)), dtype=float)
    lap = 4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return dogs, bool(lap.var() > 40)


def thumbnail(img: Image.Image):
    img = img.copy(); img.thumbnail((320, 320))
    buf = io.BytesIO(); img.save(buf, "JPEG", quality=70)  # re-encoding drops EXIF metadata
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def jpeg_bytes(img: Image.Image, size=1280, q=82):
    """Larger re-encoded copy (EXIF stripped) that officers can open to verify a report."""
    img = img.copy(); img.thumbnail((size, size))
    buf = io.BytesIO(); img.save(buf, "JPEG", quality=q); return buf.getvalue()


def status_for(conf):
    return "verified" if conf >= 0.6 else "unverified" if conf >= 0.3 else "low"


USERS, SESSIONS, NOTIFS, RATE = {}, {}, defaultdict(list), defaultdict(list)


def hash_pw(pw, salt): return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100_000).hex()


def add_user(name, email, phone, pw, role="citizen", agency=None):
    salt = secrets.token_bytes(16)
    USERS[email.lower()] = dict(name=name, email=email.lower(), phone=phone, salt=salt, hash=hash_pw(pw, salt),
                                role=role, agency=agency, points=0, false=0)


# Demo authority accounts (prototype only - use real accounts and a real database later)
add_user("MPSPK Officer", "officer@mpspk.demo", "", "demo1234", "authority", "MPSPK")
add_user("PERHILITAN Officer", "officer@perhilitan.demo", "", "demo1234", "authority", "PERHILITAN")


def need(authorization, role=None):
    tok = (authorization or "").removeprefix("Bearer ").strip()
    u = USERS.get(SESSIONS.get(tok, ""))
    if not u or (role and u["role"] != role): raise HTTPException(401, "Login required")
    return u


def user_from(authorization):
    try: return need(authorization)
    except HTTPException: return None


def limited(key, limit, window=600):
    now = time.time(); RATE[key] = [x for x in RATE[key] if now - x < window]
    if len(RATE[key]) >= limit: return True
    RATE[key].append(now); return False


def award(email, n):
    if email in USERS: USERS[email]["points"] = max(0, USERS[email]["points"] + n)


def notify(email, typ, rid, note=""):
    if email: NOTIFS[email].append(dict(id=uuid.uuid4().hex[:6], type=typ, rid=rid, note=note, ts=time.time(), read=False))


def log(r, status, by, note): r["history"].append(dict(status=status, by=by, note=note, ts=time.time()))


def get(rid): return REPORTS.get(rid) or (_ for _ in ()).throw(HTTPException(404))


def score(r):
    """Confidence triage. Never rejects a report - it only decides visibility and alerts."""
    s = 0.3 if r["category"] in ("attack", "chasing") else 0.1  # distress reports start higher
    why = []
    if r["dogs"]:
        s += 0.4 * min(1, max(r["dogs"]) / 0.6); why.append(f"dogs:{len(r['dogs'])}")
        if r["sharp"]: s += 0.05
    elif r["has_photo"] and r["left_frame"]:
        s += 0.15; why.append("left")
    elif r["animal"] == "wildlife" and r["has_photo"]:
        s += 0.2 + (0.05 if r["sharp"] else 0); why.append("wildphoto")  # the AI only recognises dogs
    elif r["has_photo"]:
        why.append("nodog")
    else:
        why.append("nophoto")
    if r["fresh"]: s += 0.10; why.append("fresh")
    if r["confirms"]: s += min(0.3, 0.15 * r["confirms"]); why.append(f"confirms:{r['confirms']}")
    if r["anonymous"]: s -= 0.1; why.append("anon")
    u = USERS.get(r["owner"] or "")
    if u and u["false"] >= 2: s -= 0.2; why.append("lowtrust")
    return round(max(0.0, min(s, 1.0)), 2), why


def refresh(r):
    r["confidence"], r["why"] = score(r)
    if r["status"] in ("verified", "unverified", "low"):  # don't overwrite authority statuses
        r["status"] = status_for(r["confidence"])
        if r["status"] == "verified" and not r.get("paid") and r["owner"]:
            r["paid"] = True; award(r["owner"], 10)


def active():
    cut = time.time() - ACTIVE_HOURS * 3600
    return [r for r in REPORTS.values() if r["status"] not in ("resolved", "false") and r["created"] > cut]


def public(r):
    return {**{k: r[k] for k in ("id", "lat", "lng", "category", "animal", "note", "status", "confidence", "why", "authority", "anonymous")},
            "dog_count": len(r["dogs"]), "age_min": int((time.time() - r["created"]) / 60), "chat": len(r["chat"]),
            "priority": SEVERITY[r["category"]] * 10 + len(r["dogs"]) * 2 + r["confidence"] * 10}


def mine(r): return {**public(r), "history": r["history"], "created": r["created"], "reopened": r.get("reopened", 0)}


def full(r): return {**mine(r), "contact": r["contact"], "thumb": r["thumb"], "open": r["status"] not in ("resolved", "false")}


def profile(u):
    return {k: u[k] for k in ("name", "email", "phone", "role", "agency", "points")} | {"unread": sum(not n["read"] for n in NOTIFS[u["email"]])}


class Signup(BaseModel): name: str; email: str; phone: str = ""; password: str
class Login(BaseModel): email: str; password: str
class Msg(BaseModel): text: str
class StatusIn(BaseModel): status: str; note: str = ""


def session(u):
    tok = secrets.token_urlsafe(24); SESSIONS[tok] = u["email"]
    return {"token": tok, "profile": profile(u)}


@app.post("/api/signup")
def signup(b: Signup):
    e = b.email.strip().lower()
    if "@" not in e or len(b.password) < 8 or not b.name.strip(): raise HTTPException(400, "Please fill in a valid name, email and an 8+ character password")
    if e in USERS: raise HTTPException(409, "This email is already registered")
    add_user(b.name.strip()[:60], e, b.phone.strip()[:20], b.password)
    return session(USERS[e])


@app.post("/api/login")
def login(b: Login):
    u = USERS.get(b.email.strip().lower())
    if not u or not secrets.compare_digest(hash_pw(b.password, u["salt"]), u["hash"]): raise HTTPException(401, "Wrong email or password")
    return session(u)


@app.get("/api/me")
def me(authorization: str | None = Header(None)): return profile(need(authorization))


@app.get("/api/notifications")
def notifications(authorization: str | None = Header(None)):
    return sorted(NOTIFS[need(authorization)["email"]], key=lambda n: -n["ts"])[:30]


@app.post("/api/notifications/read")
def read_notifications(authorization: str | None = Header(None)):
    for n in NOTIFS[need(authorization)["email"]]: n["read"] = True
    return {"ok": True}


@app.get("/api/guidance/{scenario}")
def guidance(scenario: str, lang: str = "en"):
    if scenario not in GUIDANCE: raise HTTPException(404)
    return {"steps": (GUIDANCE_MS if lang == "ms" else GUIDANCE)[scenario]}


@app.post("/api/report")
async def create_report(request: Request, lat: float = Form(...), lng: float = Form(...), category: str = Form(...),
                        animal: str = Form("dog"), note: str = Form(""), left_frame: bool = Form(False),
                        captured_at: float = Form(0), contact_phone: str = Form(""), contact_email: str = Form(""),
                        photo: UploadFile | None = File(None), authorization: str | None = Header(None)):
    if category not in SEVERITY: raise HTTPException(400, "Unknown category")
    u = user_from(authorization)
    if u and u["role"] != "citizen": u = None  # officers cannot file citizen reports
    key = u["email"] if u else request.client.host
    if limited("rep:" + key, 10 if u else 3): raise HTTPException(429, "Too many reports. Please wait a few minutes.")
    dogs, sharp, thumb, has_photo, big = [], False, None, False, None
    if photo is not None and photo.filename:
        img = Image.open(io.BytesIO(await photo.read())).convert("RGB")
        dogs, sharp = analyse(img); thumb = thumbnail(img); big = jpeg_bytes(img); has_photo = True
        if animal == "wildlife": dogs = []  # dog detector is meaningless for wildlife
    near = sum(1 for o in active() if dist_m(lat, lng, o["lat"], o["lng"]) < NEARBY_M)
    contact = dict(name=u["name"], phone=u["phone"], email=u["email"]) if u else dict(name="Anonymous", phone=contact_phone.strip()[:20], email=contact_email.strip()[:80])
    r = dict(id=uuid.uuid4().hex[:8], lat=lat, lng=lng, category=category, animal=animal, note=note[:200],
             left_frame=left_frame, dogs=dogs, sharp=sharp, has_photo=has_photo, thumb=thumb, photo=big,
             fresh=bool(captured_at) and abs(time.time() * 1000 - captured_at) < 300_000,
             confirms=near, created=time.time(), status="unverified",
             authority="PERHILITAN" if animal == "wildlife" else "MPSPK",
             owner=u["email"] if u else None, anonymous=u is None, contact=contact, chat=[], history=[], confirmers=set())
    refresh(r); log(r, "submitted", contact["name"], ""); REPORTS[r["id"]] = r
    if u: award(u["email"], 5)
    return public(r)


@app.get("/api/reports")
def list_reports():
    return sorted((public(r) for r in active()), key=lambda x: -x["priority"])


@app.get("/api/my/reports")
def my_reports(authorization: str | None = Header(None)):
    u = need(authorization, "citizen")
    return [mine(r) for r in sorted(REPORTS.values(), key=lambda r: -r["created"]) if r["owner"] == u["email"]]


@app.post("/api/reports/{rid}/confirm")
def confirm(rid: str, request: Request, authorization: str | None = Header(None)):
    r, u = get(rid), user_from(authorization)
    key = u["email"] if u else request.client.host
    if key in r["confirmers"] or key == r["owner"]: return public(r)  # one confirmation per person, none for your own report
    r["confirmers"].add(key); r["confirms"] += 1; refresh(r); return public(r)


@app.post("/api/reports/{rid}/reopen")
def reopen(rid: str, authorization: str | None = Header(None)):
    u, r = need(authorization, "citizen"), get(rid)
    if r["owner"] != u["email"] or r["status"] != "resolved": raise HTTPException(400, "Cannot reopen")
    r["status"], r["created"], r["reopened"] = "unverified", time.time(), r.get("reopened", 0) + 1
    refresh(r); log(r, "reopened", u["name"], ""); return mine(r)


@app.get("/api/reports/{rid}/chat")
def chat(rid: str): return get(rid)["chat"][-50:]


@app.post("/api/reports/{rid}/chat")
def post_chat(rid: str, b: Msg, authorization: str | None = Header(None)):
    u, r, text = need(authorization), get(rid), b.text.strip()[:200]
    if not text or limited("chat:" + u["email"], 15, 60): raise HTTPException(429, "Slow down")
    r["chat"].append(dict(name=u["name"].split()[0], role=u["role"], text=text, ts=time.time()))
    return r["chat"][-50:]


@app.get("/api/reports/{rid}/photo")
def report_photo(rid: str, authorization: str | None = Header(None)):
    u, r = need(authorization, "authority"), get(rid)
    if r["authority"] != u["agency"] or not r.get("photo"): raise HTTPException(404, "No photo")
    return Response(r["photo"], media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@app.get("/api/admin/reports")
def admin_reports(authorization: str | None = Header(None)):
    ag = need(authorization, "authority")["agency"]
    return sorted((full(r) for r in REPORTS.values() if r["authority"] == ag), key=lambda x: -x["created"])


@app.post("/api/reports/{rid}/status")
def set_status(rid: str, b: StatusIn, authorization: str | None = Header(None)):
    u, r = need(authorization, "authority"), get(rid)
    if r["authority"] != u["agency"]: raise HTTPException(403, "Not your agency")
    if b.status not in ("acknowledged", "resolved", "false", "followup"): raise HTTPException(400, "Bad status")
    note = b.note.strip()[:300]
    if b.status != "followup":
        r["status"] = b.status
        if b.status == "resolved" and r["owner"] and not r.get("paid_r"): r["paid_r"] = True; award(r["owner"], 20)
        if b.status == "false" and r["owner"]: USERS[r["owner"]]["false"] += 1; award(r["owner"], -20)
    log(r, b.status, u["agency"], note); notify(r["owner"], b.status, rid, note)
    return full(r)


@app.get("/api/stats")
def stats(authorization: str | None = Header(None)):
    ag = need(authorization, "authority")["agency"]
    rs, now = [r for r in REPORTS.values() if r["authority"] == ag], time.time()
    by_cat, hourly, cells = {}, [0] * 12, {}
    for r in rs:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
        h = int((now - r["created"]) // 3600)
        if h < 12: hourly[11 - h] += 1
        c = cells.setdefault((round(r["lat"], 3), round(r["lng"], 3)), dict(lat=0, lng=0, n=0, weight=0))
        c["lat"] += r["lat"]; c["lng"] += r["lng"]; c["n"] += 1; c["weight"] += SEVERITY[r["category"]]
    hot = sorted(({**c, "lat": c["lat"] / c["n"], "lng": c["lng"] / c["n"]} for c in cells.values()), key=lambda c: -c["weight"])[:8]
    act = [r for r in active() if r["authority"] == ag]
    return dict(total=len(rs), active=len(act), verified=sum(r["status"] == "verified" for r in act),
                unverified=sum(r["status"] in ("unverified", "low") for r in act),
                resolved=sum(r["status"] == "resolved" for r in rs), by_cat=by_cat, hourly=hourly, hotspots=hot)


@app.post("/api/seed")
def seed(authorization: str | None = Header(None)):
    """Demo data so the dashboard has something to show."""
    import random
    need(authorization, "authority")
    centers = [(5.647, 100.487), (5.655, 100.500), (5.635, 100.470)]
    for i in range(18):
        c, cat, wild = random.choice(centers), random.choice(list(SEVERITY)), i % 6 == 0
        r = dict(id=uuid.uuid4().hex[:8], lat=c[0] + random.uniform(-.004, .004), lng=c[1] + random.uniform(-.004, .004),
                 category=cat, animal="wildlife" if wild else "dog", note="Demo", left_frame=False, dogs=[] if wild else [0.8] * random.randint(0, 3),
                 sharp=True, has_photo=True, thumb=None, fresh=random.random() < .5, confirms=random.randint(0, 3),
                 created=time.time() - random.uniform(0, 8) * 3600, status="unverified",
                 authority="PERHILITAN" if wild else "MPSPK", owner=None, anonymous=True,
                 contact=dict(name="Anonymous", phone="012-3456789" if i % 2 else "", email=""), chat=[], history=[], confirmers=set())
        refresh(r); log(r, "submitted", "demo", "")
        if random.random() < .25: r["status"] = random.choice(["resolved", "false"])
        REPORTS[r["id"]] = r
    return {"ok": True}


@app.middleware("http")
async def no_cache(request: Request, call_next):
    resp = await call_next(request)
    if not request.url.path.startswith("/api"): resp.headers["Cache-Control"] = "no-store"  # always serve fresh pages
    return resp


print("Serving pages from:", BASE / "static")
app.mount("/", StaticFiles(directory=BASE / "static", html=True), name="static")