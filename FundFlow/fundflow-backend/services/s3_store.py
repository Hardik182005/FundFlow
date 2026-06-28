"""Tiny Firestore-compatible persistence layer backed by Amazon S3.

Lets all the existing `db.collection(...).document(...).set()/get()` /
`.where().stream()` / `.order_by().limit().stream()` code persist across Lambda
invocations without a database server. Enabled when AUDIT_S3_BUCKET is set;
otherwise callers fall back to in-memory.

Layout: s3://$AUDIT_S3_BUCKET/<collection>/<document>.json
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fundflow.s3")
_BUCKET = os.getenv("AUDIT_S3_BUCKET", "")
_client = None


def _s3():
    global _client
    if _client is None:
        import boto3  # bundled in the AWS Lambda Python runtime
        _client = boto3.client("s3")
    return _client


class _Doc:
    def __init__(self, data: Optional[Dict[str, Any]], doc_id: str = ""):
        self._d = data
        self.id = doc_id

    @property
    def exists(self) -> bool:
        return self._d is not None

    def to_dict(self) -> Dict[str, Any]:
        return self._d or {}


class _DocRef:
    def __init__(self, coll: str, doc_id: str):
        self.coll = coll
        self.id = doc_id

    def _key(self) -> str:
        return f"{self.coll}/{self.id}.json"

    def get(self) -> _Doc:
        try:
            obj = _s3().get_object(Bucket=_BUCKET, Key=self._key())
            return _Doc(json.loads(obj["Body"].read()), self.id)
        except Exception:
            return _Doc(None, self.id)

    def set(self, data: Dict[str, Any], merge: bool = False) -> None:
        if merge:
            cur = self.get()
            if cur.exists:
                data = {**cur.to_dict(), **data}
        _s3().put_object(Bucket=_BUCKET, Key=self._key(),
                         Body=json.dumps(data, default=str).encode("utf-8"),
                         ContentType="application/json")


class _Query:
    def __init__(self, coll: str, filters=None, limit_n=None):
        self.coll = coll
        self.filters = filters or []
        self.limit_n = limit_n

    def where(self, field, op, val):
        return _Query(self.coll, self.filters + [(field, op, val)], self.limit_n)

    def order_by(self, *a, **k):
        return self  # ordering is applied by the caller where it matters

    def limit(self, n):
        return _Query(self.coll, self.filters, n)

    def stream(self) -> List[_Doc]:
        out: List[_Doc] = []
        for doc_id, data in _list_coll(self.coll):
            ok = True
            for (f, op, v) in self.filters:
                if op == "==" and data.get(f) != v:
                    ok = False
                    break
            if ok:
                out.append(_Doc(data, doc_id))
        if self.limit_n:
            out = out[: self.limit_n]
        return out


class _Collection:
    def __init__(self, name: str):
        self.name = name

    def document(self, doc_id: str) -> _DocRef:
        return _DocRef(self.name, doc_id)

    def where(self, f, op, v) -> _Query:
        return _Query(self.name).where(f, op, v)

    def order_by(self, *a, **k) -> _Query:
        return _Query(self.name)

    def limit(self, n) -> _Query:
        return _Query(self.name).limit(n)

    def stream(self) -> List[_Doc]:
        return _Query(self.name).stream()


def _list_coll(name: str):
    items = []
    try:
        paginator = _s3().get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=_BUCKET, Prefix=f"{name}/"):
            for obj in page.get("Contents", []):
                try:
                    o = _s3().get_object(Bucket=_BUCKET, Key=obj["Key"])
                    doc_id = obj["Key"].split("/")[-1].rsplit(".json", 1)[0]
                    items.append((doc_id, json.loads(o["Body"].read())))
                except Exception:
                    continue
    except Exception as e:
        logger.warning(f"s3 list failed for {name}: {e}")
    return items


class S3Db:
    def collection(self, name: str) -> _Collection:
        return _Collection(name)


def get_db():
    """Return an S3-backed Firestore-like client, or None when no bucket is set."""
    return S3Db() if _BUCKET else None
