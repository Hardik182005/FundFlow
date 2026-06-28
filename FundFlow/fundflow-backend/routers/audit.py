"""FundFlow Audit endpoints."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import io

from models.audit_schemas import RunAuditRequest
from services import fund_audit_service as audit_svc
from services import fund_source_service as sources
from services import demo_service
from services.fund_audit_service import AuditError

logger = logging.getLogger("fundflow.router.audit")
router = APIRouter()


@router.post("/run")
async def run_audit(req: RunAuditRequest):
    try:
        return await audit_svc.run_audit(req)
    except AuditError as e:
        raise HTTPException(status_code=e.code, detail=str(e))
    except Exception as e:
        logger.exception("audit run failed")
        raise HTTPException(status_code=500, detail="The audit could not be completed. Please try again.")


@router.post("/start")
async def start_audit(req: RunAuditRequest):
    """Non-blocking start — returns an audit_id immediately (beats the 30s gateway
    cap for fresh live audits). Poll GET /api/audit/{audit_id} until status is
    'completed' or 'failed'. Supported demo funds return 'completed' right away."""
    try:
        res = audit_svc.start_audit(req)
        if res.get("status") == "inline":  # no async runtime (local dev) -> run inline
            return await audit_svc.run_audit(req, audit_id=res["audit_id"])
        return res
    except AuditError as e:
        raise HTTPException(status_code=e.code, detail=str(e))
    except Exception:
        logger.exception("audit start failed")
        raise HTTPException(status_code=500, detail="The audit could not be started. Please try again.")


@router.get("/estimate/{scheme_code}")
async def estimate(scheme_code: str, force_refresh: bool = False):
    fund = sources.get_fund(scheme_code)
    if not fund:
        raise HTTPException(status_code=404, detail="This fund is not in the source registry.")
    resolved = {k: fund[v] for k, v in audit_svc._DOC_KEYS.items() if fund.get(v)}
    return audit_svc.estimate_credits(resolved, force_refresh)


@router.get("/{audit_id}")
async def get_audit(audit_id: str):
    a = audit_svc.get_audit(audit_id) or demo_service.get_demo_audit(audit_id)
    if not a:
        raise HTTPException(status_code=404, detail="Audit not found.")
    return a


@router.get("/fund/{scheme_code}/latest")
async def latest(scheme_code: str, user_id: str = "demo-user"):
    a = audit_svc.latest_for_fund(scheme_code, user_id)
    if not a:
        raise HTTPException(status_code=404, detail="No audit found for this fund yet.")
    return a


@router.get("/user/{user_id}")
async def for_user(user_id: str):
    audits = audit_svc.audits_for_user(user_id)
    if not audits:
        audits = demo_service.demo_audit_summaries()
    return {"audits": audits}


@router.post("/{audit_id}/refresh")
async def refresh(audit_id: str):
    existing = audit_svc.get_audit(audit_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Audit not found.")
    req = RunAuditRequest(user_id="demo-user", scheme_code=existing["scheme_code"],
                          fund_name=existing["fund_name"], force_refresh=True)
    try:
        return await audit_svc.run_audit(req)
    except AuditError as e:
        raise HTTPException(status_code=e.code, detail=str(e))


@router.post("/{audit_id}/narration")
async def narration(audit_id: str):
    from services import assistant_service
    a = audit_svc.get_audit(audit_id) or demo_service.get_demo_audit(audit_id)
    if not a:
        raise HTTPException(status_code=404, detail="Audit not found.")
    script = assistant_service.build_audit_narration(a)
    return {"audit_id": audit_id, "script": script}


@router.post("/{audit_id}/report")
async def report(audit_id: str):
    from services import audit_report_service
    a = audit_svc.get_audit(audit_id) or demo_service.get_demo_audit(audit_id)
    if not a:
        raise HTTPException(status_code=404, detail="Audit not found.")
    pdf_bytes = audit_report_service.build_audit_pdf(a)
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename=fundflow-audit-{audit_id}.pdf"})
