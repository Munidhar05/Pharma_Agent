from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="JobMatch")  # JobMatch, StrongMatch, ActionRequired, Submitted, SystemAlert
    channel = Column(String(50), default="dashboard")          # dashboard, email, telegram
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), index=True, nullable=False)
    execution_id = Column(String(100), index=True, nullable=False)
    task_type = Column(String(100), nullable=False)
    status = Column(String(50), default="SUCCESS")  # SUCCESS, WARNING, FAILED, RUNNING
    items_processed = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    error_details = Column(JSON, default=dict)
    metadata_json = Column(JSON, default=dict)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    query_string = Column(String(255), nullable=False)
    filters = Column(JSON, default=dict)
    results_count = Column(Integer, default=0)
    sources_probed = Column(JSON, default=list)
    executed_at = Column(DateTime, default=datetime.utcnow)

