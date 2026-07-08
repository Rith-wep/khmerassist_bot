from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.repositories.knowledge_item import KnowledgeItemRepository
from app.schemas.knowledge import KnowledgeItemCreate, KnowledgeItemOut, KnowledgeItemUpdate

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("", response_model=list[KnowledgeItemOut])
def list_knowledge(
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[KnowledgeItemOut]:
    return KnowledgeItemRepository(db, current_user.business_id).list_ordered()


@router.post("", response_model=KnowledgeItemOut, status_code=status.HTTP_201_CREATED)
def create_knowledge(
    payload: KnowledgeItemCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeItemOut:
    item = KnowledgeItemRepository(db, current_user.business_id).create(**payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=KnowledgeItemOut)
def update_knowledge(
    item_id: int,
    payload: KnowledgeItemUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeItemOut:
    repo = KnowledgeItemRepository(db, current_user.business_id)
    item = repo.get(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge(
    item_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    repo = KnowledgeItemRepository(db, current_user.business_id)
    if not repo.delete(item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge item not found")
    db.commit()
