import requests
from .auth import TactAuth
import json
import os



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
                    print(f"{self.COOKIE_FILE} から {len(self.cookies)} 個のCookieを読み込みました")
            except Exception as e:
                print(f"Cookieの読み込みに失敗しました: {e}")

    def save_cookies(self):
        try:
            with open(self.COOKIE_FILE, 'w') as f:
                json.dump(self.cookies, f)
                print(f"Cookieを {self.COOKIE_FILE} に保存しました")
        except Exception as e:
            print(f"Cookieの保存に失敗しました: {e}")

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
