"""Tests for the optional features: auto-assignment, team, email alerts/replies (real SMTP), WhatsApp,
follow-up reminders, Excel export, summaries in the list, and the schema migration."""
import io
import socket
import sqlite3
from datetime import datetime, timedelta, timezone
from email import message_from_bytes, policy
from urllib.parse import parse_qs, urlparse

import pytest
from aiosmtpd.controller import Controller
from openpyxl import load_workbook
from sqlalchemy import create_engine, select

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.database.connection import ensure_schema
from app.models import AdminUser, Communication, Enquiry, FollowUp, WorkflowLog
from app.services.providers.base import ProviderUnavailable
from app.tests.conftest import DEFAULT_EXTRACTION


# ------------------------------------------------------------------ helpers
def add_member(db, username, role="agent", active=True):
    m = AdminUser(username=username, email=f"{username}@team.test", role=role, is_active=active,
                  password_hash=hash_password("member-pass-1", iterations=1000))
    db.add(m)
    db.commit()
    return m


def token_for(member):
    return {"Authorization": f"Bearer {create_access_token(member.username, member.role)[0]}"}


def assignee_of(db, eid):
    db.expire_all()
    return db.get(Enquiry, eid).assigned_to_id


def unique(i):
    return dict(email=f"cust{i}@example.com", phone=f"+9190000000{i:02d}", message=f"Enquiry number {i}: need something built, details {i * 7919}")


class _Capture:
    def __init__(self):
        self.messages = []

    async def handle_DATA(self, server, session, envelope):
        self.messages.append(envelope)
        return "250 Message accepted"


@pytest.fixture()
def smtp(monkeypatch):
    """A REAL local SMTP server; the app talks genuine SMTP to it (no mocking of smtplib)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    handler = _Capture()
    controller = Controller(handler, hostname="127.0.0.1", port=port)
    controller.start()
    cfg = get_settings()
    for k, v in dict(smtp_host="127.0.0.1", smtp_port=port, smtp_security="none", smtp_from="LeadFlow <leads@kiwi.test>",
                     notify_email="team@kiwi.test, boss@kiwi.test").items():
        monkeypatch.setattr(cfg, k, v)
    yield handler
    controller.stop()


def parsed(envelope):
    msg = message_from_bytes(envelope.content, policy=policy.default)
    return msg, msg.get_body(preferencelist=("plain",)).get_content().strip()


# ------------------------------------------------------------------ 8. auto-assignment
def test_new_enquiry_is_auto_assigned_and_logged(client, submit, admin, db_session):
    eid = submit()
    assert assignee_of(db_session, eid) == admin.id
    log = db_session.scalar(select(WorkflowLog).where(WorkflowLog.enquiry_id == eid, WorkflowLog.workflow_step == "team_assignment"))
    assert log.execution_status == "success" and "admin" in log.message
    row = client.get("/api/enquiries").json()["data"][0]
    assert row["assigned_to_name"] == "admin" and row["assigned_to_id"] == admin.id


def test_load_is_balanced_round_robin(client, submit, admin, db_session):
    a, b = add_member(db_session, "asha"), add_member(db_session, "bala")
    ids = [submit(**unique(i)) for i in range(6)]
    counts = {m.id: sum(assignee_of(db_session, i) == m.id for i in ids) for m in (admin, a, b)}
    assert counts == {admin.id: 2, a.id: 2, b.id: 2}


def test_least_loaded_member_gets_next_enquiry(client, submit, admin, db_session):
    a = add_member(db_session, "asha")
    first = [submit(**unique(i)) for i in range(4)]  # 2 each
    # close both of asha's enquiries -> she now has 0 open, admin has 2 open
    for i in first:
        if assignee_of(db_session, i) == a.id:
            client.put(f"/api/enquiries/{i}/status", json={"status": "Closed"})
    nxt = submit(**unique(9))
    assert assignee_of(db_session, nxt) == a.id


def test_returning_customer_keeps_same_team_member(client, submit, admin, db_session):
    a = add_member(db_session, "asha")
    first = submit(**unique(1))
    owner = assignee_of(db_session, first)
    submit(**unique(2)), submit(**unique(3))  # shift the balance elsewhere
    again = submit(email="cust1@example.com", phone="+919111111111", message="A follow-up from the same person, different words entirely")
    assert assignee_of(db_session, again) == owner
    log = db_session.scalar(select(WorkflowLog).where(WorkflowLog.enquiry_id == again, WorkflowLog.workflow_step == "team_assignment"))
    assert "returning customer" in log.message


def test_inactive_members_get_nothing_and_no_members_means_unassigned(client, submit, admin, db_session):
    sleepy = add_member(db_session, "sleepy", active=False)
    ids = [submit(**unique(i)) for i in range(3)]
    assert all(assignee_of(db_session, i) == admin.id for i in ids) and sleepy.id not in {assignee_of(db_session, i) for i in ids}
    admin.is_active = False
    db_session.commit()
    eid = submit(**unique(8))
    assert assignee_of(db_session, eid) is None
    log = db_session.scalar(select(WorkflowLog).where(WorkflowLog.enquiry_id == eid, WorkflowLog.workflow_step == "team_assignment"))
    assert log.execution_status == "skipped" and "left unassigned" in log.message


def test_manual_assign_unassign_and_filters(client, submit, admin, db_session):
    a = add_member(db_session, "asha")
    e1, e2 = submit(**unique(1)), submit(**unique(2))
    assert client.put(f"/api/enquiries/{e1}/assignee", json={"assignee_id": a.id}).json()["data"]["assigned_to_name"] == "asha"
    assert client.put(f"/api/enquiries/{e2}/assignee", json={"assignee_id": None}).json()["data"]["assigned_to_id"] is None
    assert client.put(f"/api/enquiries/{e1}/assignee", json={"assignee_id": 9999}).status_code == 404
    assert [r["id"] for r in client.get(f"/api/enquiries?assignee_id={a.id}").json()["data"]] == [e1]
    assert [r["id"] for r in client.get("/api/enquiries?unassigned=true").json()["data"]] == [e2]
    assert client.post(f"/api/enquiries/{e2}/auto-assign").json()["data"]["assigned_to_id"] is not None


# ------------------------------------------------------------------ team management
def test_team_list_shows_workload(client, submit, admin, db_session):
    add_member(db_session, "asha")
    [submit(**unique(i)) for i in range(4)]
    team = {m["username"]: m for m in client.get("/api/team").json()["data"]}
    assert team["admin"]["open_enquiries"] == 2 and team["asha"]["open_enquiries"] == 2 and team["asha"]["role"] == "agent"
    assert "password" not in str(team)


def test_admin_can_create_member_who_can_then_log_in(client, anon_client, admin):
    r = client.post("/api/team", json={"username": "new.agent", "email": "new@example.com", "password": "a-long-password", "role": "agent"})
    assert r.status_code == 201 and r.json()["data"]["role"] == "agent" and r.json()["data"]["is_active"] is True
    login = anon_client.post("/api/auth/login", json={"username": "new.agent", "password": "a-long-password"})
    assert login.status_code == 200
    dup = client.post("/api/team", json={"username": "new.agent", "email": "other@example.com", "password": "a-long-password"})
    assert dup.status_code == 409
    assert client.post("/api/team", json={"username": "x", "email": "bad", "password": "short"}).status_code == 422


def test_agents_cannot_manage_the_team(anon_client, admin, db_session):
    agent = add_member(db_session, "asha")
    h = token_for(agent)
    assert anon_client.get("/api/team", headers=h).status_code == 200  # can see who's on the team
    r = anon_client.post("/api/team", headers=h, json={"username": "sneaky", "email": "sneaky@example.org", "password": "a-long-password"})
    assert r.status_code == 403 and r.json()["success"] is False
    assert anon_client.put(f"/api/team/{agent.id}", headers=h, json={"is_active": False}).status_code == 403


def test_deactivate_member_and_safety_rules(client, admin, db_session):
    agent = add_member(db_session, "asha")
    assert client.put(f"/api/team/{agent.id}", json={"is_active": False}).json()["data"]["is_active"] is False
    assert client.put(f"/api/team/{admin.id}", json={"is_active": False}).status_code == 400  # not yourself
    assert client.put("/api/team/9999", json={"is_active": False}).status_code == 404


# ------------------------------------------------------------------ 5. email: customer replies over real SMTP
def test_send_reply_email_over_real_smtp(client, submit, smtp, db_session):
    eid = submit()
    client.put(f"/api/enquiries/{eid}/response", json={"edited_response": "Hello Rahul, this is the admin-edited reply."})
    r = client.post(f"/api/enquiries/{eid}/send-email", json={})
    assert r.status_code == 201 and r.json()["data"]["status"] == "sent" and r.json()["data"]["sent_by_name"] == "admin"
    sent = [e for e in smtp.messages if e.rcpt_tos == ["rahul@example.com"]]
    assert len(sent) == 1
    msg, body = parsed(sent[0])
    assert body == "Hello Rahul, this is the admin-edited reply."  # the EDITED version, not the AI original
    assert msg["From"] == "LeadFlow <leads@kiwi.test>" and msg["Subject"].startswith("Re: your enquiry with")
    detail = client.get(f"/api/enquiries/{eid}").json()["data"]
    assert [c["channel"] for c in detail["communications"] if c["kind"] == "customer_reply"] == ["email"]


def test_send_email_custom_subject_blocks_header_injection(client, submit, smtp):
    eid = submit()
    r = client.post(f"/api/enquiries/{eid}/send-email", json={"subject": "Hello\r\nBcc: attacker@evil.test", "body": "Custom body"})
    assert r.status_code == 201
    msg, body = parsed([e for e in smtp.messages if e.rcpt_tos == ["rahul@example.com"]][0])
    assert msg["Bcc"] is None and "\n" not in msg["Subject"] and body == "Custom body"


def test_send_email_errors_are_clear_not_fake(client, submit, db_session, monkeypatch):
    eid = submit()
    r = client.post(f"/api/enquiries/{eid}/send-email", json={})  # SMTP not configured in tests
    assert r.status_code == 409 and r.json()["error"]["code"] == "email_not_configured"
    assert db_session.scalar(select(Communication.id)) is None  # nothing was claimed as sent


def test_send_email_failure_is_recorded(client, submit, smtp, monkeypatch, db_session):
    eid = submit()
    monkeypatch.setattr(get_settings(), "smtp_port", 1)  # nothing listens here
    r = client.post(f"/api/enquiries/{eid}/send-email", json={})
    assert r.status_code == 502 and r.json()["error"]["code"] == "email_failed"
    assert "smtp" in r.json()["error"]["message"].lower() or "email" in r.json()["error"]["message"].lower()
    c = db_session.scalars(select(Communication).where(Communication.channel == "email", Communication.kind == "customer_reply")).one()
    assert c.status == "failed" and c.error


def test_send_email_needs_an_email_address_and_a_reply(client, submit, smtp, fake):
    phone_only = client.post("/api/enquiries", json={"customer_name": "P", "phone": "+919000000000", "message": "phone only enquiry about a website"}).json()["data"]["id"]
    assert client.post(f"/api/enquiries/{phone_only}/send-email", json={}).status_code == 409
    fake.script["extraction"] = [ProviderUnavailable("x")] * 3
    no_reply = submit(**unique(5))
    r = client.post(f"/api/enquiries/{no_reply}/send-email", json={})
    assert r.status_code == 409 and "no reply text" in r.json()["error"]["message"].lower()


# ------------------------------------------------------------------ 5. email: team alerts
def test_team_alert_sent_for_urgent_enquiry_once(client, submit, smtp, fake, admin, db_session):
    fake.extraction = {**DEFAULT_EXTRACTION, "urgency": "High"}  # -> High priority
    eid = submit()
    to = {addr for e in smtp.messages for addr in e.rcpt_tos}
    assert to == {"admin@example.com", "team@kiwi.test", "boss@kiwi.test"}  # assignee + team inboxes
    msg, body = parsed(smtp.messages[0])
    assert f"#{eid}" in msg["Subject"] and "E-commerce Development" in msg["Subject"]
    assert "Priority:  High" in body and f"/admin/enquiries/{eid}" in body and "Customer requires an e-commerce website." in body
    log = db_session.scalar(select(WorkflowLog).where(WorkflowLog.enquiry_id == eid, WorkflowLog.workflow_step == "email_notification"))
    assert log.execution_status == "success"
    # re-analysis must not spam the team again
    before = len(smtp.messages)
    client.post(f"/api/enquiries/{eid}/reanalyze")
    assert len(smtp.messages) == before
    note = db_session.scalars(select(WorkflowLog).where(WorkflowLog.enquiry_id == eid, WorkflowLog.workflow_step == "email_notification").order_by(WorkflowLog.id.desc())).first()
    assert note.execution_status == "skipped" and "already notified" in note.message


def test_non_urgent_enquiry_only_alerts_the_assignee(client, submit, smtp, fake):
    fake.extraction = {**DEFAULT_EXTRACTION, "urgency": "Low", "budget": None, "currency": None, "requirements": ["x"], "confidence": 0.8}
    submit()
    assert {addr for e in smtp.messages for addr in e.rcpt_tos} == {"admin@example.com"}


def test_alert_failure_never_breaks_the_workflow(client, submit, smtp, monkeypatch, db_session):
    monkeypatch.setattr(get_settings(), "smtp_port", 1)
    eid = submit()
    e = db_session.get(Enquiry, eid)
    assert e.ai_status == "completed"  # AI result still saved
    steps = {l.workflow_step: l for l in db_session.scalars(select(WorkflowLog).where(WorkflowLog.enquiry_id == eid))}
    assert steps["email_notification"].execution_status == "failed" and "workflow_completed" in steps


def test_alerts_skipped_cleanly_when_email_not_configured(client, submit, db_session):
    eid = submit()
    log = db_session.scalar(select(WorkflowLog).where(WorkflowLog.enquiry_id == eid, WorkflowLog.workflow_step == "email_notification"))
    assert log.execution_status == "skipped" and "not configured" in log.message


def test_capabilities_reflect_configuration(client, smtp, monkeypatch):
    assert client.get("/api/system/capabilities").json()["data"] == {"email_enabled": True, "whatsapp_enabled": True, "default_country_code": "91"}
    monkeypatch.setattr(get_settings(), "smtp_host", None)
    assert client.get("/api/system/capabilities").json()["data"]["email_enabled"] is False


# ------------------------------------------------------------------ 4. WhatsApp click-to-chat
def test_whatsapp_link_prefilled_with_the_reply(client, submit, db_session):
    eid = submit()  # phone +91 98765 43210 -> normalised +919876543210
    r = client.post(f"/api/enquiries/{eid}/whatsapp", json={})
    assert r.status_code == 201
    link = r.json()["data"]["link"]
    u = urlparse(link)
    assert (u.scheme, u.netloc, u.path) == ("https", "wa.me", "/919876543210")
    reply = client.get(f"/api/enquiries/{eid}").json()["data"]["response"]["final_response"]
    assert parse_qs(u.query)["text"][0] == reply
    comm = r.json()["data"]["communication"]
    assert comm["channel"] == "whatsapp" and comm["status"] == "opened" and comm["recipient"] == "+919876543210"  # honest: opened, not "sent"


def test_whatsapp_adds_default_country_code_and_uses_edited_reply(client, submit):
    eid = submit(phone="9811122233")
    client.put(f"/api/enquiries/{eid}/response", json={"edited_response": "नमस्ते! Edited & ready."})
    link = client.post(f"/api/enquiries/{eid}/whatsapp", json={}).json()["data"]["link"]
    u = urlparse(link)
    assert u.path == "/919811122233" and parse_qs(u.query)["text"][0] == "नमस्ते! Edited & ready."
    custom = client.post(f"/api/enquiries/{eid}/whatsapp", json={"text": "Just a custom line"}).json()["data"]["link"]
    assert parse_qs(urlparse(custom).query)["text"][0] == "Just a custom line"


def test_whatsapp_requires_phone_and_reply(client, submit, fake):
    email_only = client.post("/api/enquiries", json={"customer_name": "E", "email": "e@example.com", "message": "email only enquiry"}).json()["data"]["id"]
    assert client.post(f"/api/enquiries/{email_only}/whatsapp", json={}).status_code == 409
    fake.script["extraction"] = [ProviderUnavailable("x")] * 3
    no_reply = submit(**unique(4))
    assert client.post(f"/api/enquiries/{no_reply}/whatsapp", json={}).status_code == 409


# ------------------------------------------------------------------ 3. follow-up reminders
def test_followups_listed_across_enquiries_with_context(client, submit, admin):
    e1 = submit(**unique(1))
    submit(**unique(2))
    body = client.get("/api/followups").json()
    assert body["meta"]["total"] >= 2 and body["data"]
    item = next(i for i in body["data"] if i["enquiry_id"] == e1)
    assert item["customer_name"] == "Rahul Sharma" and item["assigned_to_name"] == "admin" and item["status"] == "Pending"
    assert item["suggested_date"] and item["is_overdue"] is False
    dates = [i["suggested_date"] for i in body["data"] if i["suggested_date"]]
    assert dates == sorted(dates)  # most urgent first


def test_overdue_followups_flagged_and_filterable(client, submit, db_session):
    eid = submit()
    fu = db_session.scalars(select(FollowUp).where(FollowUp.enquiry_id == eid)).first()
    fu.suggested_date = datetime.now(timezone.utc) - timedelta(days=2)
    db_session.commit()
    overdue = client.get("/api/followups?overdue=true").json()
    assert [i["id"] for i in overdue["data"]] == [fu.id] and overdue["data"][0]["is_overdue"] is True
    s = client.get("/api/followups/summary").json()["data"]
    assert s["overdue"] == 1 and s["pending"] >= 1


def test_mark_followup_done_dismissed_and_reopen(client, submit):
    submit()
    fid = client.get("/api/followups").json()["data"][0]["id"]
    s = client.put(f"/api/followups/{fid}", json={"status": "Done"}).json()["data"]
    assert s["done"] == 1
    assert fid not in [i["id"] for i in client.get("/api/followups").json()["data"]]  # default view = Pending
    assert fid in [i["id"] for i in client.get("/api/followups?status=Done").json()["data"]]
    client.put(f"/api/followups/{fid}", json={"status": "Pending"})
    assert fid in [i["id"] for i in client.get("/api/followups").json()["data"]]
    assert client.put(f"/api/followups/{fid}", json={"status": "Nonsense"}).status_code == 422
    assert client.put("/api/followups/99999", json={"status": "Done"}).status_code == 404


def test_followups_filter_by_assignee(client, submit, admin, db_session):
    a = add_member(db_session, "asha")
    ids = [submit(**unique(i)) for i in range(2)]
    mine = [i for i in ids if assignee_of(db_session, i) == a.id][0]
    got = client.get(f"/api/followups?assignee_id={a.id}").json()["data"]
    assert got and {g["enquiry_id"] for g in got} == {mine}


# ------------------------------------------------------------------ 9. Excel export
def test_excel_export_is_a_real_workbook(client, submit):
    submit()
    r = client.get("/api/enquiries/export?format=xlsx")
    assert r.status_code == 200 and "spreadsheetml" in r.headers["content-type"] and r.headers["content-disposition"].endswith('enquiries.xlsx"')
    wb = load_workbook(io.BytesIO(r.content))
    ws = wb["Enquiries"]
    header = [c.value for c in ws[1]]
    assert header[:3] == ["Id", "Customer Name", "Email"] and "Summary" in header and "Assigned To" in header and "Lead Score" in header
    row = dict(zip(header, [c.value for c in ws[2]]))
    assert row["Customer Name"] == "Rahul Sharma" and row["Service Category"] == "E-commerce Development"
    assert row["Budget"] == 50000 and row["Assigned To"] == "admin" and row["Summary"] == "Customer requires an e-commerce website."


def test_excel_export_respects_filters_and_blocks_formulas(client, submit):
    submit(customer_name='=HYPERLINK("http://evil.test","click")')
    submit(**unique(2))
    ws = load_workbook(io.BytesIO(client.get("/api/enquiries/export?format=xlsx").content))["Enquiries"]
    assert ws.max_row == 3
    cell = next(c for row in ws.iter_rows(min_row=2) for c in row if isinstance(c.value, str) and "HYPERLINK" in c.value)
    assert cell.data_type == "s" and cell.value.startswith("=HYPERLINK")  # stored as TEXT, never a formula
    only_closed = load_workbook(io.BytesIO(client.get("/api/enquiries/export?format=xlsx&status=Closed").content))["Enquiries"]
    assert only_closed.max_row == 1  # header only
    assert client.get("/api/enquiries/export?format=pdf").status_code == 422
    assert client.get("/api/enquiries/export").headers["content-type"].startswith("text/csv")  # default unchanged


def test_export_endpoints_require_login(anon_client):
    assert anon_client.get("/api/enquiries/export?format=xlsx").status_code == 401


# ------------------------------------------------------------------ 10. summaries visible in the list
def test_ai_summary_is_in_list_items_and_searchable(client, submit):
    submit()
    row = client.get("/api/enquiries").json()["data"][0]
    assert row["summary"] == "Customer requires an e-commerce website."
    assert client.get("/api/enquiries?search=requires an e-commerce").json()["meta"]["total"] == 1


# ------------------------------------------------------------------ migration for existing databases
def test_schema_migration_upgrades_an_old_database_in_place(tmp_path):
    db_file = tmp_path / "old.db"
    con = sqlite3.connect(db_file)
    con.executescript("""
        CREATE TABLE admin_users (id INTEGER PRIMARY KEY, username VARCHAR(50), email VARCHAR(254), password_hash VARCHAR(255), role VARCHAR(20), created_at DATETIME);
        CREATE TABLE enquiries (id INTEGER PRIMARY KEY, customer_name VARCHAR(150), message TEXT, status VARCHAR(20));
        INSERT INTO admin_users VALUES (1, 'old-admin', 'o@x.test', 'hash', 'admin', '2026-01-01');
        INSERT INTO enquiries VALUES (1, 'Existing Customer', 'old message', 'New');
    """)
    con.commit()
    con.close()
    engine = create_engine(f"sqlite:///{db_file}")
    applied = ensure_schema(engine)
    assert set(applied) == {"enquiries.assigned_to_id", "enquiries.assigned_at", "admin_users.is_active"}
    assert ensure_schema(engine) == []  # idempotent
    con = sqlite3.connect(db_file)
    assert con.execute("SELECT is_active FROM admin_users").fetchone() == (1,)  # existing admins stay active
    assert con.execute("SELECT customer_name, assigned_to_id FROM enquiries").fetchone() == ("Existing Customer", None)  # data intact
    engine.dispose()
