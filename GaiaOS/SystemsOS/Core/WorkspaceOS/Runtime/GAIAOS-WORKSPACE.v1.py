#!/usr/bin/env python3
"""Bounded GaiaOS workspace artifact runtime."""
from __future__ import annotations
import hashlib, json, os, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.getenv("GAIAOS_WORKSPACE_ROOT","/data/gaiaos-workspace")).resolve()

def _now(): return datetime.now(timezone.utc).isoformat()

def _safe(name: str) -> Path:
    p=(ROOT/name).resolve()
    p.relative_to(ROOT)
    return p

def write_artifact(name: str, content: str, provenance: str, approved: bool=False) -> dict:
    if not approved: return {"status":"HOLD","reason":"explicit Naomi approval required","effect_authority":"NONE"}
    path=_safe(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    digest=hashlib.sha256(content.encode("utf-8")).hexdigest()
    receipt={"receipt_id":f"ART-{uuid.uuid4().hex}","timestamp":_now(),"path":str(path),"sha256":digest}
    return {"status":"EXECUTED","artifact":{"name":name,"sha256":digest,"provenance":provenance},"receipt":receipt}

def read_artifact(name: str) -> dict:
    path=_safe(name)
    if not path.is_file(): return {"status":"UNKNOWN","reason":"artifact not found","name":name}
    content=path.read_text(encoding="utf-8")
    return {"status":"OBSERVED","name":name,"content":content,"sha256":hashlib.sha256(content.encode("utf-8")).hexdigest()}
