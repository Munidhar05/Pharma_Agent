import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.database import Base
from backend.app.models.user import User, UserPreferences
from backend.app.models.audit import Notification
from backend.app.agents.notification import NotificationAgent
from backend.app.services.scheduler import AutonomousScheduler
from backend.app.schemas.notification import NotificationBatchReadRequest
from backend.app.api.v1.notifications import (
    list_notifications,
    get_unread_count,
    mark_notification_as_read,
    mark_all_notifications_read,
    get_scheduler_status
)


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    user = User(
        email="rajesh.pharma@feuji.com",
        password_hash="hashed_pw_123",
        full_name="Rajesh Sharma",
        role="candidate"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    prefs = UserPreferences(
        user_id=user.id,
        notification_channels=["dashboard"],
        min_match_score_alert=70
    )
    db.add(prefs)
    db.commit()

    try:
        yield db
    finally:
        db.close()


def test_notification_agent_dispatch_and_milestones(test_db):
    """Test NotificationAgent creates in-app notifications and milestone alerts."""
    user = test_db.query(User).first()
    agent = NotificationAgent(test_db)

    # 1. High match alert
    notifs = agent.notify_high_match(
        user_id=user.id,
        job_title="Associate Data Engineer",
        company_name="Dr. Reddy's Laboratories",
        match_score=88.5,
        job_id=1
    )
    assert len(notifs) >= 1
    assert notifs[0].notification_type == "StrongMatch"
    assert "89%" in notifs[0].title or "88%" in notifs[0].title
    assert notifs[0].is_read is False

    # 2. Awaiting approval alert
    notifs2 = agent.notify_awaiting_approval(
        user_id=user.id,
        job_title="Associate Data Engineer",
        company_name="Dr. Reddy's Laboratories",
        app_id=1
    )
    assert notifs2[0].notification_type == "ActionRequired"
    assert "Approval" in notifs2[0].title

    # 3. Interview scheduled alert
    notifs3 = agent.notify_interview_scheduled(
        user_id=user.id,
        job_title="Associate Data Engineer",
        company_name="Dr. Reddy's Laboratories",
        notes="HR scheduled Technical Round via MS Teams."
    )
    assert notifs3[0].notification_type == "Interview"
    assert "Interview" in notifs3[0].title

    # 4. Assessment alert
    notifs4 = agent.notify_assessment_pending(
        user_id=user.id,
        job_title="Associate Data Engineer",
        company_name="Dr. Reddy's Laboratories"
    )
    assert notifs4[0].notification_type == "Assessment"

    # Total in DB
    total = test_db.query(Notification).filter(Notification.user_id == user.id).count()
    assert total == 4


def test_notifications_api_endpoints(test_db):
    """Test Notification REST API route handlers."""
    user = test_db.query(User).first()
    agent = NotificationAgent(test_db)

    agent.notify_high_match(
        user_id=user.id,
        job_title="Data Analyst",
        company_name="Novartis",
        match_score=82.0,
        job_id=2
    )
    agent.notify_application_confirmed(
        user_id=user.id,
        job_title="Data Analyst",
        company_name="Novartis",
        ref_id="REF-NOV-001"
    )

    # 1. List
    records = list_notifications(user_id=user.id, db=test_db)
    assert len(records) >= 2

    # 2. Unread count
    unread = get_unread_count(user_id=user.id, db=test_db)
    assert unread["unread_count"] >= 2

    first_notif = records[0]

    # 3. Mark single as read
    marked = mark_notification_as_read(id=first_notif.id, db=test_db)
    assert marked.is_read is True

    unread_after = get_unread_count(user_id=user.id, db=test_db)
    assert unread_after["unread_count"] == unread["unread_count"] - 1

    # 4. Batch mark all read
    batch_req = NotificationBatchReadRequest()
    batch_resp = mark_all_notifications_read(request=batch_req, user_id=user.id, db=test_db)
    assert "marked as read" in batch_resp["message"]

    unread_final = get_unread_count(user_id=user.id, db=test_db)
    assert unread_final["unread_count"] == 0


def test_scheduler_status_and_lifecycle():
    """Test AutonomousScheduler status reporting."""
    scheduler = AutonomousScheduler()
    status = scheduler.get_status()

    assert "tasks" in status
    assert "job_discovery" in status["tasks"]
    assert "job_verification" in status["tasks"]
    assert "candidate_matching" in status["tasks"]
    assert "company_discovery" in status["tasks"]

    # Verify task intervals
    assert status["tasks"]["job_discovery"]["interval_hours"] == 6
    assert status["tasks"]["job_verification"]["interval_hours"] == 12

    # Test API status endpoint
    api_status = get_scheduler_status()
    assert "tasks" in api_status
