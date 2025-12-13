from typing import List, Dict, Any, Set
import requests
import logging
from bs4 import BeautifulSoup
from ..core.session import session_manager

logger = logging.getLogger(__name__)

class TactAPI:
    BASE_URL = "https://tact.ac.thers.ac.jp"
    
    def __init__(self):
        self.session_manager = session_manager

    def _get(self, endpoint: str) -> Dict[str, Any]:
        try:
            session = self.session_manager.get_session()
            url = f"{self.BASE_URL}{endpoint}"
            response = session.get(url)
            response.raise_for_status()

            # レスポンスからCookieを更新（Sticky Session維持など）
            self.session_manager.update_cookies(response.cookies)

            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {endpoint}: {e}", exc_info=True)
            raise

    def _get_text(self, endpoint: str) -> str:
        try:
            session = self.session_manager.get_session()
            url = f"{self.BASE_URL}{endpoint}"
            response = session.get(url)
            response.raise_for_status()

            # レスポンスからCookieを更新（Sticky Session維持など）
            self.session_manager.update_cookies(response.cookies)

            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch text from {endpoint}: {e}", exc_info=True)
            raise


    def get_favorite_site_ids(self) -> Set[str]:
        """
        ポータルページをスクレイピングしてお気に入りサイトのIDを取得します。
        """
        try:
            html = self._get_text("/portal")
            soup = BeautifulSoup(html, "lxml")
            # トップナビゲーション内にあるクラス 'Mrphs-sitesNav__favbtn' のボタンを探す
            # これらが実際のお気に入りサイトを表している
            buttons = soup.find_all(class_="Mrphs-sitesNav__favbtn")
            fav_ids = set()
            for btn in buttons:
                sid = btn.get("data-site-id")
                if sid:
                    fav_ids.add(sid)
            return fav_ids
        except Exception as e:
            logger.error(f"お気に入りの取得エラー: {e}", exc_info=True)
            return set()

    def get_sites(self) -> List[Dict[str, Any]]:
        """
        現在のユーザーのサイト（コース/プロジェクト）一覧を取得します。
        Sakai Entity Provider: /direct/site.json を使用します。
        /portal からスクレイピングしたお気に入り状況とマージします。
        """
        # メモ: /direct/site.json は全てのサイトを返す可能性がある
        # /direct/site/user.json の方が良い場合もあるが、まずは標準的なものを試す
        data = self._get("/direct/site.json?_limit=200")
        all_sites = data.get('site_collection', [])
        
        fav_ids = self.get_favorite_site_ids()
        
        # サイトの処理とフィルタリング
        # 必要な情報: id, title, url, is_favorite
        processed_sites = []
        for site in all_sites:
            site_id = site.get('id')
            # 一貫性と可用性を確保するため、IDからURLを構築する
            # Sakaiの 'url' フィールドは欠けていたり、特定のページを指している場合がある
            # プレフィックス + ID で構築する
            site_url = site.get('url')
            if not site_url and site_id:
                site_url = f"{self.BASE_URL}/portal/site/{site_id}"
            
            processed_sites.append({
                "id": site_id,
                "title": site.get('title'),
                "url": site_url,
                "is_favorite": site_id in fav_ids
            })
            
        return processed_sites

    def get_my_assignments(self) -> List[Dict[str, Any]]:
        """
        現在のユーザーの課題を取得します。
        Endpoint: /direct/assignment/my.json
        """
        data = self._get("/direct/assignment/my.json")
        return data.get('assignment_collection', [])

    def get_site_resources(self, site_id: str) -> List[Dict[str, Any]]:
        """
        特定のサイトのリソースを取得します。
        Endpoint: /direct/content/site/{site_id}.json
        """
        data = self._get(f"/direct/content/site/{site_id}.json")
        return data.get('content_collection', [])

    def get_announcements(self) -> List[Dict[str, Any]]:
        """
        お知らせ (Motd/Notices) を取得します。
        Endpoint: /direct/announcement/user.json
        """
        data = self._get("/direct/announcement/user.json")
        return data.get('announcement_collection', [])

tact_api = TactAPI()
