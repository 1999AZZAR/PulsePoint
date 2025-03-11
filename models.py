from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import datetime

db = SQLAlchemy()

# Association table for many-to-many relationship between Query and Tag
query_tag_association = db.Table(
    "query_tag_association",
    db.Column("query_id", db.Integer, db.ForeignKey("queries.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class Query(db.Model):
    __tablename__ = "queries"  # Explicitly set table name

    id = db.Column(db.Integer, primary_key=True)
    query_text = db.Column(db.String(255), nullable=False, unique=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    source_control = db.Column(db.JSON, nullable=True)  # Track source control values
    gemini_processed = db.Column(
        db.Boolean, default=False
    )  # Track if Gemini has processed this query

    # Relationships
    results = relationship(
        "Result", back_populates="query", cascade="all, delete-orphan"
    )
    tags = relationship(
        "Tag", secondary=query_tag_association, back_populates="queries"
    )
    gemini_response = relationship(
        "GeminiResponse",
        back_populates="query",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(
        db.String(100), nullable=False, unique=True
    )  # Ensure tags are unique

    # Relationships
    queries = relationship(
        "Query", secondary=query_tag_association, back_populates="tags"
    )


class Result(db.Model):
    __tablename__ = "results"

    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(
        db.Integer, db.ForeignKey("queries.id", ondelete="CASCADE"), nullable=False
    )
    source = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255))
    snippet = db.Column(db.Text)
    url = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Add timestamp field
    sentiment_score = db.Column(db.Float, nullable=True)  # Add sentiment score field

    # Relationship
    query = relationship("Query", back_populates="results")


class GeminiResponse(db.Model):
    __tablename__ = "gemini_responses"

    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(
        db.Integer,
        db.ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    summary = db.Column(db.Text)
    insights = db.Column(db.Text)
    cross_references = db.Column(db.Text)
    tags = db.Column(db.Text)  # Stored as a comma-separated string or JSON

    # Relationship
    query = relationship("Query", back_populates="gemini_response")
