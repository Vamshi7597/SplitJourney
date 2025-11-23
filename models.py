"""
SQLAlchemy models for SplitJourney.
Defines the data structure for Users, Groups, Expenses, Chat, and Polls.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
import sqlalchemy
from datetime import datetime
from core.db import Base

class User(Base):
    """
    Represents a registered user of the application.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # Relationships
    created_groups = relationship("Group", back_populates="creator")
    # Note: We don't directly link User to GroupMember here to avoid circular complexity,
    # but we can query it.

    def __repr__(self):
        return f"<User(name='{self.name}', email='{self.email}')>"

class Group(Base):
    """
    Represents a group of users sharing expenses.
    """
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    budget_amount = Column(Float, nullable=True)  # Optional group budget

    # Relationships
    creator = relationship("User", back_populates="created_groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Group(name='{self.name}')>"

class GroupMember(Base):
    """
    Represents a member of a group.
    Can be linked to a registered User, or just be a name (for non-registered friends).
    """
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    member_name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    group = relationship("Group", back_populates="members")
    # user relationship is optional if we want to access the User object
    
    # Expenses paid by this member
    expenses_paid = relationship("Expense", back_populates="payer_member")
    # Splits owed by this member
    expense_splits = relationship("ExpenseSplit", back_populates="member")

    def __repr__(self):
        return f"<GroupMember(name='{self.member_name}', group_id={self.group_id})>"

class Expense(Base):
    """
    Represents a single expense paid by a member in a group.
    """
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    payer_member_id = Column(Integer, ForeignKey("group_members.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    group = relationship("Group", back_populates="expenses")
    payer_member = relationship("GroupMember", back_populates="expenses_paid")
    splits = relationship("ExpenseSplit", back_populates="expense", cascade="all, delete-orphan")
    place_tag = relationship("PlaceTag", back_populates="expense", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Expense(desc='{self.description}', amount={self.amount})>"

class ExpenseSplit(Base):
    """
    Represents how much a specific member owes for a specific expense.
    """
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("group_members.id"), nullable=False)
    amount_owed = Column(Float, nullable=False)

    # Relationships
    expense = relationship("Expense", back_populates="splits")
    member = relationship("GroupMember", back_populates="expense_splits")

    def __repr__(self):
        return f"<ExpenseSplit(member_id={self.member_id}, owed={self.amount_owed})>"

class Settlement(Base):
    """
    Represents a payment made between two members to settle debts.
    """
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    payer_member_id = Column(Integer, ForeignKey("group_members.id"), nullable=False)
    receiver_member_id = Column(Integer, ForeignKey("group_members.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Settlement(payer={self.payer_member_id}, receiver={self.receiver_member_id}, amount={self.amount})>"

class Message(Base):
    """
    Represents a chat message in a group.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    sender_member_id = Column(Integer, ForeignKey("group_members.id"), nullable=False)
    text = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("Group")
    sender = relationship("GroupMember")

    def __repr__(self):
        return f"<Message(group_id={self.group_id}, sender={self.sender_member_id}, text='{self.text[:20]}...')>"

class Poll(Base):
    """
    Represents a poll created in a group.
    """
    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    question = Column(String, nullable=False)
    created_by_member_id = Column(Integer, ForeignKey("group_members.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    group = relationship("Group")
    creator = relationship("GroupMember")
    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    votes = relationship("PollVote", back_populates="poll", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Poll(id={self.id}, question='{self.question}')>"

class PollOption(Base):
    """
    Represents an option in a poll.
    """
    __tablename__ = "poll_options"

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    text = Column(String, nullable=False)

    # Relationships
    poll = relationship("Poll", back_populates="options")
    votes = relationship("PollVote", back_populates="option", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PollOption(poll_id={self.poll_id}, text='{self.text}')>"

class PollVote(Base):
    """
    Represents a vote on a poll option by a member.
    One vote per member per poll constraint.
    """
    __tablename__ = "poll_votes"
    __table_args__ = (
        # Ensure one vote per member per poll
        sqlalchemy.UniqueConstraint('poll_id', 'member_id', name='unique_member_vote_per_poll'),
    )

    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"), nullable=False)
    option_id = Column(Integer, ForeignKey("poll_options.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("group_members.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    poll = relationship("Poll", back_populates="votes")
    option = relationship("PollOption", back_populates="votes")
    member = relationship("GroupMember")

    def __repr__(self):
        return f"<PollVote(poll_id={self.poll_id}, option_id={self.option_id}, member_id={self.member_id})>"

class PlaceTag(Base):
    """
    Represents a Google Place tagged to an expense.
    """
    __tablename__ = "place_tags"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False, unique=True)
    place_id = Column(String, nullable=False)  # Google place_id
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    expense = relationship("Expense", back_populates="place_tag")

    def __repr__(self):
        return f"<PlaceTag(expense_id={self.expense_id}, name='{self.name}')>"
