# type: ignore

from typing import Optional, Union

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app_be.database.db import get_db
from app_be.models.db_models import Chapter, Content, Topic
from app_be.services import content_service

router = APIRouter()


@router.get("/chapters")
def list_chapters(db: Session = Depends(get_db)) -> list[Chapter]:
    return content_service.get_all_chapters(db)


@router.get("/chapters/{chapter_id}")
def get_chapter(chapter_id: int, db: Session = Depends(get_db)) -> Optional[Chapter]:
    return content_service.get_chapter_by_id(db, chapter_id, with_topics=True)


@router.get("/topics")
def list_topics(db: Session = Depends(get_db)) -> list[Topic]:
    return content_service.get_all_topics(db, with_content=False)


@router.get("/topics/{topic_id}")
def get_topic(topic_id: int, db: Session = Depends(get_db)) -> Optional[Topic]:
    return content_service.get_topic_by_id(db, topic_id, with_content=False)


@router.get("/topics/{topic_id}/contents")
def get_contents_for_topic(
    topic_id: int, db: Session = Depends(get_db)
) -> list[Content]:
    return content_service.get_content_for_topic(db, topic_id)


@router.get("/search")
def search(
    query: str = Query(..., min_length=1), db: Session = Depends(get_db)
) -> dict[str, list[Union[Topic, Content]]]:
    return content_service.search_topics_and_content(db, query)
