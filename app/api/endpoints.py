from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from ..services.tact_api import tact_api
from ..core.session import session_manager

router = APIRouter()

@router.post("/auth/login")
async def login():
    """
    Playwrightによる認証フローをトリガーする。
    サーバーサイドでブラウザ（ヘッドレス）を起動する。
    """
    try:
        await session_manager.authenticate(headless=False)
        return {"message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



class Site(BaseModel):
    id: str
    title: str | None = None
    url: str
    is_favorite: bool

@router.get("/sites", response_model=list[Site])
def get_sites():
    try:
        sites = tact_api.get_sites()
        return sites
    except Exception as e:
        # e は単なるprint出力かもしれないが、500エラーを返すようにする
        logger.error(f"Error fetching sites: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sites/{site_id}/favorite")
def add_favorite_site(site_id: str):
    """
    指定されたサイトをお気に入りに追加する。
    """
    try:
        success = tact_api.add_favorite_site(site_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add favorite site")
        return {"message": f"Site {site_id} added to favorites"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding favorite site: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sites/{site_id}/favorite")
def remove_favorite_site(site_id: str):
    """
    指定されたサイトをお気に入りから削除する。
    """
    try:
        success = tact_api.remove_favorite_site(site_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to remove favorite site")
        return {"message": f"Site {site_id} removed from favorites"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite site: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
