import requests
from typing import Dict
from .auth import TactAuth
import json
import os
import logging

logger = logging.getLogger(__name__)



class TactSession:
    _instance = None
    COOKIE_FILE = "cookies.json"
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TactSession, cls).__new__(cls)
            cls._instance.cookies: Dict[str, str] = {}
            cls._instance.headers: Dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            cls._instance.load_cookies()
        return cls._instance

    def load_cookies(self):
        if os.path.exists(self.COOKIE_FILE):
            try:
                with open(self.COOKIE_FILE, 'r') as f:
                    self.cookies = json.load(f)
                    logger.info(f"{self.COOKIE_FILE} から {len(self.cookies)} 個のCookieを読み込みました")
            except Exception as e:
                logger.error(f"Cookieの読み込みに失敗しました。ファイルが破損しているか、権限がありません: {e}")
                logger.warning("再認証を行ってください。")
                self.cookies = {}

    def save_cookies(self):
        try:
            # Open the file with 0600 permissions (owner read/write only)
            flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
            mode = 0o600
            fd = os.open(self.COOKIE_FILE, flags, mode)
            with os.fdopen(fd, 'w') as f:
                json.dump(self.cookies, f)
                logger.info(f"Cookieを {self.COOKIE_FILE} に保存しました")
            # Ensure permissions are set even if file existed before
            os.chmod(self.COOKIE_FILE, 0o600)
        except Exception as e:
            logger.error(f"Cookieの保存に失敗しました: {e}")
            raise e

    def update_cookies(self, new_cookies: requests.cookies.RequestsCookieJar):
        """
        APIレスポンスなどから得られた新しいCookieで内部状態を更新し、ファイルに保存する。
        特にAWSALBなどのSticky Session用Cookieや、再発行されたJSESSIONIDを維持するために使用。
        """
        if not new_cookies:
            return

        updated = False
        for name, value in new_cookies.items():
            if self.cookies.get(name) != value:
                self.cookies[name] = value
                updated = True
                # ログレベルはDEBUG推奨だが、挙動確認のため一時的にINFOにする
                logger.info(f"Cookie updated: {name}") 
        
        if updated:
            self.save_cookies()

    def get_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(self.headers)
        session.cookies.update(self.cookies)
        return session

    async def authenticate(self, headless: bool = False):
        auth = TactAuth(headless=headless)
        self.cookies = await auth.login()
        self.save_cookies()

session_manager = TactSession()
