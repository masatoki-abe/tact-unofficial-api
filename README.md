# TACT 非公式 API

TACT (東海国立大学機構 / 名古屋大学 LMS) の非公式APIです。
FastAPIとPlaywrightを使用し、ブラウザベースのSSO認証を介してLMSのデータにアクセスします。

## 特徴

*   **SAML認証対応**: Microsoft OnlineのSSO/MFA（多要素認証）をPlaywrightによるブラウザ操作で通過します。
*   **セッション永続化**: ログイン後のCookieを `cookies.json` に保存し、次回以降は再ログインなしで高速に動作します。
*   **お気に入り判定**: TACTポータル上のお気に入りバーを解析し、よく使う講義サイトを識別します。
*   **クリーンなデータ**: 複雑なSakaiのレスポンスを整理し、必要な情報（ID, タイトル, URLなど）のみを提供します。

## エンドポイント

| メソッド | パス | 説明 |
| :--- | :--- | :--- |
| `POST` | `/auth/login` | ブラウザを起動してログインフローを開始します。手動での認証操作が必要です。 |
| `GET` | `/sites` | 受講している講義サイトの一覧を取得します。 |

## クイックスタート

### 前提条件
*   Python 3.10+
*   Google Chrome / Chromium (Playwright用)

### インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd tact-unofficial-api

# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
playwright install chromium
```

### 実行方法

```bash
# サーバーの起動
./run_server.sh
# または
uvicorn app.main:app --reload
```

APIドキュメントは `http://localhost:8000/docs` で確認できます。

### 使い方

1.  初めて使用する場合、サーバーを起動後に `POST /auth/login` を実行してください。
2.  サーバー側でブラウザが起動します。Microsoftのログイン画面が表示されるので、ログインと多要素認証を完了してください。
3.  ログインが完了するとブラウザが自動的に閉じ、セッション情報が `cookies.json` に保存されます。
4.  以降は `GET /sites` などのAPIを呼び出すことができます。

## 注意事項

このプロジェクトは非公式であり、大学当局とは一切関係ありません。
TACT (Sakai) の仕様変更により、予告なく動作しなくなる可能性があります。
自己責任で利用してください。
