import csv

from sqlalchemy.orm import Session

from app_be.database.db import Base, SessionLocal, engine
from app_be.models.db_models import Chapter, Content, Topic  # type: ignore


def init_sample_topics(db: Session) -> dict[int, Topic]:
    """Load chapters and topics from topics.csv into the database"""
    chapters_by_name: dict[str, Chapter] = {}

    with open(
        "app_be/textbooks/linear_algebra_topics.csv",
        mode="r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            chapter_title = row["chapter"]
            topic_name = row["name"]
            chapter_order = int(row["chapter_order"]) if row["chapter_order"] else 0
            chapter_id = int(row["chapter_id"]) if row["chapter_id"] else None
            topic_id = int(row["topic_id"]) if row["topic_id"] else None

            # Check if Chapter already created (locally)
            chapter = chapters_by_name.get(chapter_title)
            if not chapter:
                chapter = Chapter(id=chapter_id, title=chapter_title)
                db.add(chapter)
                chapters_by_name[chapter_title] = chapter

            # Create Topic
            topic = Topic(
                id=topic_id,
                name=topic_name,
                chapter=chapter,
                chapter_order=chapter_order,
            )
            db.add(topic)

    db.commit()

    # Return a map of topic_id to Topic object for use when creating Content
    topics = db.query(Topic).all()
    topic_dict = {topic.id: topic for topic in topics}
    return topic_dict


def init_sample_content(db: Session, topic_dict: dict[int, Topic]) -> None:
    """Load content from content.csv into the database"""
    with open(
        "app_be/textbooks/linear_algebra_content.csv",
        mode="r",
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            topic_id = int(row["topic_id"]) if row["topic_id"] else None
            if topic_id not in topic_dict:
                print(
                    f"""Warning: topic_id {topic_id} not found in topics.
                    Skipping content '{row['title']}'."""
                )
                continue

            content = Content(
                title=row["title"],
                latex_content=row.get("latex_content"),
                text_content=row["text_content"],
                content_type=row["content_type"],
                topic_id=topic_id,
            )
            db.add(content)

    db.commit()


def create_tables() -> None:
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables() -> None:
    """Drop all database tables - USE WITH CAUTION"""
    Base.metadata.drop_all(bind=engine)


def init_db(should_drop: bool = False) -> None:
    """Initialize the database with tables and optional sample data"""
    if should_drop:
        print("Dropping existing tables...")
        drop_tables()

    print("Creating tables...")
    create_tables()

    db = SessionLocal()
    try:
        print("Adding sample topics and chapters...")
        topic_dict = init_sample_topics(db)

        print("Adding sample content...")
        init_sample_content(db, topic_dict)

        print("Database initialization complete!")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db(should_drop=True)
