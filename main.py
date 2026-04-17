from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json, threading, uuid, secrets, os
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_kilit = threading.Lock()
_veri = {"kullanicilar": {}, "gruplar": {}, "maclar": {}, "grup_mesajlari": {}, "aktiviteler": {}}

def _kaydet():
    pass  # Koyeb'de dosya sistemi geçici — memory yeterli

@app.get("/")
def ana(): return {"durum": "aktif", "sunucu": "Matematik Asistani Sosyal Sunucu"}

@app.get("/durum")
def durum(): return {"aktif": True}

@app.post("/sosyal/kullanici_kaydet")
def kullanici_kaydet(g: dict):
    kid, adi = g.get("id",""), g.get("adi","")
    if not kid or not adi: return {"basarili": False}
    with _kilit: _veri["kullanicilar"][kid] = {"id": kid, "adi": adi, "son_giris": datetime.now().isoformat()}
    return {"basarili": True}

@app.get("/sosyal/kullanici_ara")
def kullanici_ara(sorgu: str = ""):
    with _kilit:
        for k, v in _veri["kullanicilar"].items():
            if v.get("adi","").lower() == sorgu.lower() or k == sorgu:
                return {"bulunan": v}
    return {"bulunan": None}

@app.post("/sosyal/grup_olustur")
def grup_olustur(g: dict):
    kod = secrets.token_hex(3).upper()
    gid = str(uuid.uuid4())[:8]
    oid, oadi = g.get("olusturan_id",""), g.get("olusturan_adi","")
    with _kilit:
        _veri["gruplar"][gid] = {"id": gid, "adi": g.get("adi","Grup"), "kod": kod,
            "olusturan": oid, "olusturan_adi": oadi,
            "olusturma": datetime.now().isoformat(), "aktif": True,
            "siralama": {oid: {"adi": oadi, "puan": 0}}}
        _veri["grup_mesajlari"][gid] = []
    return {"basarili": True, "grup_id": gid, "kod": kod}

@app.get("/sosyal/grup_bul")
def grup_bul(kod: str = ""):
    with _kilit:
        for g in _veri["gruplar"].values():
            if g.get("kod","").upper() == kod.upper(): return {"bulunan": g}
    return {"bulunan": None}

@app.get("/sosyal/grup_bilgi")
def grup_bilgi(grup_id: str = ""):
    with _kilit: return {"grup": _veri["gruplar"].get(grup_id)}

@app.post("/sosyal/gruba_katil")
def gruba_katil(g: dict):
    gid, kid, adi = g.get("grup_id",""), g.get("kullanici_id",""), g.get("adi","")
    with _kilit:
        if gid in _veri["gruplar"]:
            _veri["gruplar"][gid]["siralama"][kid] = {"adi": adi, "puan": 0}
    return {"basarili": True}

@app.post("/sosyal/mesaj_gonder")
def mesaj_gonder(g: dict):
    gid = g.get("grup_id","")
    with _kilit:
        if gid not in _veri["grup_mesajlari"]: _veri["grup_mesajlari"][gid] = []
        _veri["grup_mesajlari"][gid].append({
            "gonderen_id": g.get("gonderen_id",""), "gonderen_adi": g.get("gonderen_adi",""),
            "icerik": g.get("icerik",""), "tur": "metin", "tarih": datetime.now().isoformat()})
        _veri["grup_mesajlari"][gid] = _veri["grup_mesajlari"][gid][-200:]
    return {"basarili": True}

@app.get("/sosyal/grup_mesajlari")
def grup_mesajlari(grup_id: str = ""):
    with _kilit: return {"mesajlar": _veri["grup_mesajlari"].get(grup_id, [])[-100:]}

@app.get("/sosyal/grup_siralama")
def grup_siralama(grup_id: str = ""):
    with _kilit:
        s = _veri["gruplar"].get(grup_id, {}).get("siralama", {})
        return {"siralama": sorted([{"kullanici_id": k, **v} for k,v in s.items()], key=lambda x: x.get("puan",0), reverse=True)}

@app.post("/sosyal/grup_puan_ekle")
def grup_puan_ekle(g: dict):
    gid, kid, adi, puan = g.get("grup_id",""), g.get("kullanici_id",""), g.get("adi",""), int(g.get("puan",0))
    with _kilit:
        if gid in _veri["gruplar"]:
            s = _veri["gruplar"][gid].setdefault("siralama", {})
            m = s.get(kid, {"adi": adi, "puan": 0})
            m["puan"] = m.get("puan",0) + puan
            s[kid] = m
    return {"basarili": True}

@app.get("/sosyal/aktif_gruplar")
def aktif_gruplar():
    with _kilit:
        return {"gruplar": sorted([g for g in _veri["gruplar"].values() if g.get("aktif")], key=lambda x: x.get("olusturma",""), reverse=True)[:20]}

@app.post("/sosyal/mac_olustur")
def mac_olustur(g: dict):
    kod = secrets.token_hex(3).upper()
    mid = str(uuid.uuid4())[:8]
    oid, oadi = g.get("olusturan_id",""), g.get("olusturan_adi","")
    with _kilit:
        _veri["maclar"][mid] = {"id": mid, "kod": kod, "olusturan": oid, "olusturan_adi": oadi,
            "olusturma": datetime.now().isoformat(), "aktif": True,
            "siralama": {oid: {"adi": oadi, "puan": 0}}}
    return {"basarili": True, "mac_id": mid, "kod": kod}

@app.get("/sosyal/mac_bul")
def mac_bul(kod: str = ""):
    with _kilit:
        for m in _veri["maclar"].values():
            if m.get("kod","").upper() == kod.upper(): return {"bulunan": m}
    return {"bulunan": None}

@app.get("/sosyal/mac_bilgi")
def mac_bilgi(mac_id: str = ""):
    with _kilit: return {"mac": _veri["maclar"].get(mac_id)}

@app.post("/sosyal/maca_katil")
def maca_katil(g: dict):
    mid, kid, adi = g.get("mac_id",""), g.get("kullanici_id",""), g.get("adi","")
    with _kilit:
        if mid in _veri["maclar"]:
            _veri["maclar"][mid]["siralama"][kid] = {"adi": adi, "puan": 0}
    return {"basarili": True}

@app.get("/sosyal/mac_siralama")
def mac_siralama(mac_id: str = ""):
    with _kilit:
        s = _veri["maclar"].get(mac_id, {}).get("siralama", {})
        return {"siralama": sorted([{"kullanici_id": k, **v} for k,v in s.items()], key=lambda x: x.get("puan",0), reverse=True)}

@app.post("/sosyal/mac_puan_ekle")
def mac_puan_ekle(g: dict):
    mid, kid, adi, puan = g.get("mac_id",""), g.get("kullanici_id",""), g.get("adi",""), int(g.get("puan",0))
    with _kilit:
        if mid in _veri["maclar"]:
            s = _veri["maclar"][mid].setdefault("siralama", {})
            m = s.get(kid, {"adi": adi, "puan": 0})
            m["puan"] = m.get("puan",0) + puan
            s[kid] = m
    return {"basarili": True}

@app.get("/sosyal/aktif_maclar")
def aktif_maclar():
    with _kilit:
        return {"maclar": sorted([m for m in _veri["maclar"].values() if m.get("aktif")], key=lambda x: x.get("olusturma",""), reverse=True)[:20]}

@app.post("/sosyal/aktivite_paylas")
def aktivite_paylas(g: dict):
    kid = g.get("kullanici_id","")
    with _kilit:
        if kid not in _veri["aktiviteler"]: _veri["aktiviteler"][kid] = []
        _veri["aktiviteler"][kid].append({**g, "tarih": datetime.now().isoformat()})
        _veri["aktiviteler"][kid] = _veri["aktiviteler"][kid][-20:]
    return {"basarili": True}

@app.post("/sosyal/arkadas_aktiviteleri")
def arkadas_aktiviteleri(g: dict):
    ids = g.get("arkadas_ids", [])
    sonuc = []
    with _kilit:
        for kid in ids[:20]:
            sonuc.extend(_veri["aktiviteler"].get(kid, [])[-5:])
    sonuc.sort(key=lambda x: x.get("tarih",""), reverse=True)
    return {"aktiviteler": sonuc[:50]}
