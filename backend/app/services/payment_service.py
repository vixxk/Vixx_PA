"""
Payment Service — All payment CRUD + PDF generation.
"""
import dateutil.parser
import uuid as uuid_mod
import os
import re
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.project import Project
from app.models.payment import Payment
from app.services.entity_resolver import resolve_project_from_context
from app.services.analytics_service import invalidate_analytics_cache
import logging

logger = logging.getLogger(__name__)


async def _get_user_projects_and_ids(db, user_id):
    proj_stmt = select(Project).filter(Project.user_id == user_id)
    proj_result = await db.execute(proj_stmt)
    projects = proj_result.scalars().all()
    return projects, [p.id for p in projects]


async def _find_project(db, user_id, proj_title, raw_input, session_data=None):
    projects, _ = await _get_user_projects_and_ids(db, user_id)
    if not projects:
        return None, projects
    project = await resolve_project_from_context(db, user_id, raw_input, extracted_title=proj_title, session_data=session_data)
    return project, projects


async def list_payments(db, user_id, project_title=None, raw_input="", session_data=None):
    project, projects = await _find_project(db, user_id, project_title, raw_input, session_data)
    lower_input = raw_input.lower()
    wants_finished = any(w in lower_input for w in ["finished", "completed", "done"])
    wants_active = any(w in lower_input for w in ["active", "planning", "developing", "in progress"])

    if project:
        stmt = select(Payment, Project.title).join(Project).filter(Payment.project_id == project.id).order_by(Payment.received_date.desc())
    else:
        stmt = select(Payment, Project.title).join(Project).filter(Project.user_id == user_id)
        if wants_finished and not wants_active:
            stmt = stmt.filter(Project.status.in_(["finished", "completed"]))
        elif wants_active and not wants_finished:
            stmt = stmt.filter(Project.status.notin_(["finished", "completed"]))
        stmt = stmt.order_by(Payment.received_date.desc())

    rows = (await db.execute(stmt)).all()
    
    if not rows:
        if project and project.total_amount is not None:
            return (
                f"### 💳 Payment Status for project '{project.title}':\n\n"
                f"- **Total Amount (Budget)**: {project.total_amount:,.2f} INR\n"
                f"- **Payment Received**: 0.00 INR\n"
                f"- **Remaining Payment**: {project.total_amount:,.2f} INR\n"
            )
        return "No payment records found."

    if project:
        msg = f"### 💳 Payments Logged for project '{project.title}':\n\n"
    elif wants_finished and not wants_active:
        msg = "### 💳 Payments Logged (Finished Projects):\n\n"
    elif wants_active and not wants_finished:
        msg = "### 💳 Payments Logged (Active Projects):\n\n"
    else:
        msg = "### 💳 Payments Logged:\n\n"

    total_received = 0
    for p_row, proj_title_str in rows:
        date_str = p_row.received_date.strftime("%Y-%m-%d") if p_row.received_date else "N/A"
        se = "✅" if p_row.status == "received" else "⏳" if p_row.status == "pending" else "❌"
        msg += f"- **{proj_title_str}**: {p_row.amount:,.2f} {p_row.currency} ({p_row.payment_type}) on {date_str} {se} *Note: {p_row.notes or 'None'}*\n"
        if p_row.status == "received":
            total_received += p_row.amount

    if project and project.total_amount is not None:
        remaining_payment = project.total_amount - total_received
        msg += (
            f"\n**Total Amount (Budget)**: {project.total_amount:,.2f} INR\n"
            f"**Payment Received**: {total_received:,.2f} INR\n"
            f"**Remaining Payment**: {remaining_payment:,.2f} INR\n"
        )
    else:
        total_all = sum(p_row.amount for p_row, _ in rows)
        msg += f"\n**Total Payments Logged**: {total_all:,.2f} INR equivalent (approx)\n"
        msg += f"**Total Payments Received**: {total_received:,.2f} INR equivalent (approx)\n"

    return msg


async def create_payment(db, user_id, payment_data, raw_input="", session_data=None):
    from app.utils.validators import validate_payment_amount, validate_currency
    
    project, projects = await _find_project(db, user_id, payment_data.get("project_title"), raw_input, session_data)
    if not project:
        if not projects:
            project = Project(user_id=user_id, title=payment_data.get("project_title") or "General Projects", description="Auto-created.", status="active")
            db.add(project)
            await db.flush()
        else:
            project = projects[0]

    payments_to_create = []
    if "payments" in payment_data and isinstance(payment_data["payments"], list) and payment_data["payments"]:
        payments_to_create = payment_data["payments"]
    else:
        payments_to_create = [payment_data]

    created_payments = []
    for p_item in payments_to_create:
        amount = p_item.get("amount")
        valid, err = validate_payment_amount(amount)
        if not valid:
            continue
        # Force currency to INR as all transactions are in rupees only
        currency = "INR"
            
        rec_dt = None
        if p_item.get("received_date"):
            try: rec_dt = dateutil.parser.parse(p_item["received_date"])
            except: pass
        if not rec_dt: rec_dt = datetime.utcnow()
        
        p_type = p_item.get("payment_type")
        if p_type:
            p_type_lower = str(p_type).lower()
            if "advance" in p_type_lower:
                p_type = "Advance"
            elif "final" in p_type_lower:
                p_type = "Final"
            elif "partial" in p_type_lower or "installment" in p_type_lower or "milestone" in p_type_lower:
                p_type = "Partial"
            else:
                p_type = str(p_type).capitalize()
        else:
            existing_p_stmt = select(Payment).filter(Payment.project_id == project.id)
            existing_p_res = await db.execute(existing_p_stmt)
            has_existing = len(existing_p_res.scalars().all()) > 0
            p_type = "Partial" if has_existing else "Advance"

        p_status = p_item.get("status") or "received"
        if p_status:
            status_lower = str(p_status).lower()
            if status_lower in ["paid", "completed", "received", "success"]:
                p_status = "received"
            elif status_lower in ["pending", "unpaid", "due"]:
                p_status = "pending"
            elif status_lower in ["overdue", "late"]:
                p_status = "overdue"

        new_p = Payment(
            project_id=project.id,
            amount=amount,
            currency=currency,
            payment_type=p_type,
            received_date=rec_dt,
            status=p_status,
            notes=p_item.get("notes")
        )
        db.add(new_p)
        created_payments.append(new_p)
        
    if not created_payments:
        valid, err = validate_payment_amount(payment_data.get("amount"))
        if not valid: return err
        valid, err = validate_currency(payment_data.get("currency"))
        if not valid: return err
        return "No valid payments specified."
        
    await db.commit()
    invalidate_analytics_cache(user_id)
    
    for new_payment in created_payments:
        await db.refresh(new_payment)
        
    if len(created_payments) == 1:
        return f"Successfully logged payment of {created_payments[0].amount} {created_payments[0].currency} ({created_payments[0].payment_type}) for project '{project.title}'."
    else:
        return f"Successfully logged {len(created_payments)} payments for project '{project.title}'."


async def update_payment(db, user_id, payment_data, raw_input="", session_data=None):
    project, projects = await _find_project(db, user_id, payment_data.get("project_title"), raw_input, session_data)
    if not project:
        return "Project not found."
        
    stmt = select(Payment).filter(Payment.project_id == project.id).order_by(Payment.received_date.asc())
    payments_list = (await db.execute(stmt)).scalars().all()
    
    if not payments_list:
        return await create_payment(db, user_id, payment_data, raw_input, session_data)
        
    updates = []
    if "payments" in payment_data and isinstance(payment_data["payments"], list) and payment_data["payments"]:
        updates = payment_data["payments"]
    else:
        updates = [payment_data]
        
    updated_count = 0
    # Keep track of updated payment IDs to prevent updating the same payment multiple times in a batch
    updated_ids = set()
    
    for up_item in updates:
        p_obj = None
        
        # 1. Match by payment_type if provided
        target_type = up_item.get("payment_type")
        if target_type:
            for p in payments_list:
                if p.id not in updated_ids and str(p.payment_type or "").lower() == target_type.lower():
                    p_obj = p
                    break
                    
        # 2. Match by amount if provided
        if not p_obj and up_item.get("amount") is not None:
            for p in payments_list:
                if p.id not in updated_ids and abs(float(p.amount) - float(up_item["amount"])) < 0.01:
                    p_obj = p
                    break
                    
        # 3. Fallback to index matching if updates length matches list length
        if not p_obj and len(updates) == len(payments_list):
            try:
                idx = updates.index(up_item)
                if idx < len(payments_list):
                    candidate = payments_list[idx]
                    if candidate.id not in updated_ids:
                        p_obj = candidate
            except ValueError:
                pass
                
        # 4. Ultimate fallback: if there's only one payment and it hasn't been updated yet
        if not p_obj and len(payments_list) == 1 and payments_list[0].id not in updated_ids:
            p_obj = payments_list[0]
            
        if p_obj:
            updated_ids.add(p_obj.id)
            if up_item.get("amount") is not None: p_obj.amount = up_item["amount"]
            if up_item.get("status") is not None:
                status_val = str(up_item["status"]).lower()
                if status_val in ["paid", "completed", "received", "success"]:
                    p_obj.status = "received"
                elif status_val in ["pending", "unpaid", "due"]:
                    p_obj.status = "pending"
                elif status_val in ["overdue", "late"]:
                    p_obj.status = "overdue"
                else:
                    p_obj.status = up_item["status"]
            if up_item.get("payment_type") is not None: p_obj.payment_type = up_item["payment_type"]
            if up_item.get("notes") is not None: p_obj.notes = up_item["notes"]
            if up_item.get("received_date") is not None:
                try: p_obj.received_date = dateutil.parser.parse(up_item["received_date"])
                except: pass
            updated_count += 1
            
    if updated_count > 0:
        await db.commit()
        invalidate_analytics_cache(user_id)
        return f"Updated {updated_count} payment(s) for project '{project.title}'."
        
    return "No matching payment record found to update."


async def delete_payment(db, user_id, payment_data=None, raw_input="", session_data=None, confirmed=False):
    if not confirmed:
        return {"needs_confirmation": True, "message": "⚠️ Are you sure you want to delete the last payment record? Please choose Yes or No."}
    project, projects = await _find_project(db, user_id, (payment_data or {}).get("project_title"), raw_input, session_data)
    _, proj_ids = await _get_user_projects_and_ids(db, user_id)
    if project:
        stmt = select(Payment).filter(Payment.project_id == project.id).order_by(Payment.created_at.desc())
    else:
        stmt = select(Payment).filter(Payment.project_id.in_(proj_ids)).order_by(Payment.created_at.desc())
    payment_obj = (await db.execute(stmt)).scalars().first()
    if payment_obj:
        amount = payment_obj.amount
        await db.delete(payment_obj)
        await db.commit()
        invalidate_analytics_cache(user_id)
        return {"needs_confirmation": False, "message": f"Deleted last payment record of {amount}."}
    return {"needs_confirmation": False, "message": "No payment record found to delete."}


async def generate_payments_pdf(db, user_id, raw_input="", project_title=None, session_data=None):
    from app.utils.pdf_generator import generate_payments_report_pdf
    project, projects = await _find_project(db, user_id, project_title, raw_input, session_data)
    if project:
        stmt = select(Payment, Project.title).join(Project).filter(Payment.project_id == project.id).order_by(Payment.received_date.desc())
    else:
        stmt = select(Payment, Project.title).join(Project).filter(Project.user_id == user_id).order_by(Payment.received_date.desc())
    rows = (await db.execute(stmt)).all()
    if not rows: return "No payment records found to generate a PDF report."
    raw_lower = raw_input.lower()
    status_filter = next((s for s in ["pending","received","overdue"] if f"only {s}" in raw_lower or f"status {s}" in raw_lower), None)
    since_date = None
    dm = re.search(r"since\s+(\d{4}-\d{2}-\d{2})", raw_lower)
    if dm:
        try: since_date = dateutil.parser.parse(dm.group(1)).date()
        except: pass
    data_list = []
    for p_row, ptitle in rows:
        if status_filter and str(p_row.status or "").lower() != status_filter: continue
        p_date = p_row.received_date or p_row.due_date
        if since_date and p_date and p_date.date() < since_date: continue
        data_list.append({"project_title": ptitle, "amount": p_row.amount, "currency": p_row.currency, "payment_type": p_row.payment_type, "status": p_row.status, "received_date": p_row.received_date, "due_date": p_row.due_date, "notes": p_row.notes})
    if not data_list: return "No payments matched your filters."
    theme = next((t for t in ["teal","emerald","charcoal","ruby"] if t in raw_lower), "navy")
    title_val = "Payments & Cashflow Report"
    tm = re.search(r"title\s+['\"](.+?)['\"]", raw_input, re.IGNORECASE)
    if tm: title_val = tm.group(1)
    elif "invoice" in raw_lower: title_val = "Invoice Summary Report"
    elif project: title_val = f"Payments Report: {project.title}"
    exclude_notes = "exclude notes" in raw_lower or "without notes" in raw_lower or "no notes" in raw_lower
    uid = uuid_mod.uuid4().hex[:8]
    fname = f"uploads/payments_report_{uid}.pdf"
    os.makedirs("uploads", exist_ok=True)
    generate_payments_report_pdf(data_list, fname, {"title": title_val, "subtitle": f"Total records: {len(data_list)}", "theme": theme, "exclude_notes": exclude_notes, "total_amount": project.total_amount if project else None})
    url = f"http://localhost:8000/{fname}"
    tbl = "\n### 💳 Payment Details:\n\n| Project | Date | Type | Status | Amount |\n| :--- | :--- | :--- | :--- | :--- |\n"
    for i in data_list:
        dt = i["received_date"] or i["due_date"]
        ds = dt.strftime("%Y-%m-%d") if dt else "-"
        se = "✅" if str(i["status"]).upper() == "RECEIVED" else "⏳"
        tbl += f"| **{i['project_title']}** | {ds} | {i['payment_type']} | {se} {str(i['status']).upper()} | **{i['amount']:,} {i['currency']}** |\n"
    return f"### 📄 PDF Report Generated!\n\nUsing **{theme.upper()}** theme.\n- **Title**: {title_val}\n- **Records**: {len(data_list)}\n\n📥 **[Download PDF]({url})**\n{tbl}"
