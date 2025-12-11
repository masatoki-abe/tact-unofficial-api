import asyncio
from playwright.async_api import async_playwright, BrowserContext
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TactAuth:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async def login(self) -> Dict[str, str]:
        """
        ログイン用のブラウザを起動し、Cookieを辞書として返す。
        ユーザーがログインプロセス（対話が必要な場合）を完了するまでブロックする。
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(user_agent=self.user_agent)
            
            page = await context.new_page()
            
            # TACTログインページへ移動
            await page.goto("https://tact.ac.thers.ac.jp/portal/login")
            
            # ログイン成功を示す特定の要素を待機する
            # Sakai/TACTでは、通常URLがportalに戻るか、特定の要素が存在するようになる
            
            logger.info("ログイン待機中... ブラウザを手動で閉じないでください。")
            logger.info("ログインが検知されるとブラウザは自動的に閉じます。")
            
            # TACTポータルへのリダイレクトを待機
            try:
                # ユーザーのログイン（MFA等）のために最大5分待機
                # URLに '/portal' が含まれることを確認し、LMSに戻ったことを検知する
                await page.wait_for_url("**/portal**", timeout=300000, wait_until="domcontentloaded")
                logger.info("ログインを検知しました！Cookieを取得中...")
            except Exception as e:
                logger.error(f"ログインがタイムアウトしたか、リダイレクトの検知に失敗しました。現在のURL: {page.url}")
                logger.error(f"エラー: {e}")
                await browser.close()
                raise e

            # Cookieの取得
            cookies = await context.cookies()
            logger.info(f"{len(cookies)} 個のCookieを取得しました。")
            cookie_dict = {c['name']: c['value'] for c in cookies}
            
            await browser.close()
            return cookie_dict

if __name__ == "__main__":
    auth = TactAuth(headless=False)
    cookies = asyncio.run(auth.login())
    print("Captured Cookies:", cookies)
