# type: ignore

from typing import Optional, Union

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app_be.database.db import get_db
from app_be.models.schemas import (
    ChapterOut,
    ContentOut,
    TopicOut,
)
from app_be.services import content_service

router = APIRouter()


@router.get("/chapters", response_model=list[ChapterOut])
def list_chapters(db: Session = Depends(get_db)):
    return content_service.get_all_chapters(db)


@router.get("/chapters/{chapter_id}", response_model=Optional[ChapterOut])
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    chapter = content_service.get_chapter_by_id(db, chapter_id, with_topics=True)
    return chapter


@router.get("/topics", response_model=list[TopicOut])
def list_topics(db: Session = Depends(get_db)):
    return content_service.get_all_topics(db, with_content=False)


@router.get("/topics/{topic_id}", response_model=Optional[TopicOut])
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = content_service.get_topic_by_id(db, topic_id, with_content=False)
    return topic


@router.get("/topics/{topic_id}/contents", response_model=list[ContentOut])
def get_contents_for_topic(topic_id: int, db: Session = Depends(get_db)):
    return content_service.get_content_for_topic(db, topic_id)


@router.get("/search", response_model=dict[str, list[Union[TopicOut, ContentOut]]])
def search(
    query: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    return content_service.search_topics_and_content(db, query)
