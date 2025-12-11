from fastapi import APIRouter, HTTPException

from ..services.tact_api import tact_api
from ..core.session import session_manager

router = APIRouter()

@router.post("/auth/login")
async def login():
    """
    Playwrightによる認証フローをトリガーします。
    サーバーサイドでブラウザ（ヘッドレス）を起動します。
    """
    try:
        await session_manager.authenticate(headless=False)
        return {"message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel

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
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
