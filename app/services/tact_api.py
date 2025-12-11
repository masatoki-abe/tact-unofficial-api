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
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch text from {endpoint}: {e}", exc_info=True)
            raise


    
    def _post(self, endpoint: str, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        try:
            session = self.session_manager.get_session()
            url = f"{self.BASE_URL}{endpoint}"
            response = session.post(url, data=data, **kwargs)
            response.raise_for_status()
            # レスポンスがJSONでない場合もあるため、content-typeを確認するか、
            # エラー時にテキストを返すなどの対応が必要だが、一旦JSONを期待する
            try:
                return response.json()
            except ValueError:
                return {"text": response.text}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to post to {endpoint}: {e}", exc_info=True)
            raise

    def _get_csrf_token(self) -> str:
        """
        ポータルページからCSRFトークンを取得する。
        Sakaiでは通常 'sakai_csrf_token' という名前で埋め込まれています。
        """
        try:
            # ポータルページを取得 (軽量なのは /portal/site/~... だが、/portal で汎用的に)
            html = self._get_text("/portal")
            soup = BeautifulSoup(html, "lxml")
            # <input type="hidden" name="sakai_csrf_token" value="..." /> を探す
            token_input = soup.find("input", {"name": "sakai_csrf_token"})
            if token_input and token_input.get("value"):
                return token_input.get("value")
            
            # 見つからない場合はログを出して空文字を返す (後続のリクエストで失敗する可能性が高い)
            logger.warning("CSRF token not found in /portal")
            return ""
        except Exception as e:
            logger.error(f"Failed to get CSRF token: {e}", exc_info=True)
            return ""

    def get_favorite_site_ids(self) -> Set[str]:
        """
        お気に入りサイトのID一覧を取得する。
        Endpoint: /portal/favorites/list
        """
        try:
            data = self._get("/portal/favorites/list")
            # response data structure:
            # { "favoriteSiteIds": ["id1", "id2"], "autoFavoritesEnabled": true }
            return set(data.get("favoriteSiteIds", []))
        except Exception as e:
            logger.error(f"Failed to get favorite sites: {e}", exc_info=True)
            return set()

    def _update_favorites(self, site_ids: Set[str]) -> bool:
        """
        お気に入りサイトリストを更新する。
        Endpoint: /portal/favorites/update
        """
        try:
            endpoint = "/portal/favorites/update"
            # 現在の設定（autoFavoritesEnabled）を維持するため、まずは現状を取得したいが、
            # 簡易的に True (デフォルト) または現状維持で送る必要がある。
            # GET時のレスポンスに autoFavoritesEnabled が含まれているはず。
            
            # 再取得して autoFavoritesEnabled を確認
            current_data = self._get("/portal/favorites/list")
            auto_enabled = current_data.get("autoFavoritesEnabled", True)

            payload = {
                "userFavorites": {
                    "favoriteSiteIds": list(site_ids),
                    "autoFavoritesEnabled": auto_enabled
                }
            }
            
            # JSONではなくForm Dataとして送信されている: userFavorites={JSON string}
            # requestsのdata引数に辞書を渡すとForm Dataになる
            import json
            form_data = {
                "userFavorites": json.dumps(payload["userFavorites"])
            }
            
            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Origin": self.BASE_URL,
                "Referer": f"{self.BASE_URL}/portal"
            }
            
            self._post(endpoint, data=form_data) # _postにheaders引数がないので追加する必要がある
            
            return True
        except Exception as e:
            logger.error(f"Failed to update favorites: {e}", exc_info=True)
            return False

    def add_favorite_site(self, site_id: str) -> bool:
        """
        サイトをお気に入りに追加する。
        """
        try:
            fav_ids = self.get_favorite_site_ids()
            if site_id in fav_ids:
                return True # 既に登録済み
            
            fav_ids.add(site_id)
            return self._update_favorites(fav_ids)
        except Exception as e:
            logger.error(f"Failed to add favorite site {site_id}: {e}", exc_info=True)
            return False

    def remove_favorite_site(self, site_id: str) -> bool:
        """
        サイトをお気に入りから削除する。
        """
        try:
            fav_ids = self.get_favorite_site_ids()
            if site_id not in fav_ids:
                return True # 既に削除済み
            
            fav_ids.remove(site_id)
            return self._update_favorites(fav_ids)
        except Exception as e:
            logger.error(f"Failed to remove favorite site {site_id}: {e}", exc_info=True)
            return False

    def get_sites(self) -> List[Dict[str, Any]]:
        """
        現在のユーザーのサイト（コース/プロジェクト）一覧を取得する。
        Sakai Entity Provider: /direct/site.json を使用する。
        /portal からスクレイピングしたお気に入り状況とマージする。
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
        現在のユーザーの課題を取得する。
        Endpoint: /direct/assignment/my.json
        """
        data = self._get("/direct/assignment/my.json")
        return data.get('assignment_collection', [])

    def get_site_resources(self, site_id: str) -> List[Dict[str, Any]]:
        """
        特定のサイトのリソースを取得する。
        Endpoint: /direct/content/site/{site_id}.json
        """
        data = self._get(f"/direct/content/site/{site_id}.json")
        return data.get('content_collection', [])

    def get_announcements(self) -> List[Dict[str, Any]]:
        """
        お知らせ (Motd/Notices) を取得する。
        Endpoint: /direct/announcement/user.json
        """
        data = self._get("/direct/announcement/user.json")
        return data.get('announcement_collection', [])

tact_api = TactAPI()
