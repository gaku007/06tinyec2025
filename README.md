# ApparelShop — 開発セットアップ & 実行ガイド

このリポジトリは `req.md` と `design.md` に基づく簡易アパレルECデモです。Python (Flask) で実装された最小構成のWebアプリが `web_app/` 配下にあります。

目次
- 前提
- 仮想環境作成 (.venv)
- 依存インストール
- 開発サーバ起動
- 本番風に起動（gunicorn）
- テストと動作確認
- よくあるトラブルと対処

前提
- macOS / zsh を想定。Python 3.8+ がインストールされていることを確認してください。

1) 仮想環境作成（プロジェクトルート）

ターミナルでリポジトリのルートに移動して実行してください。

```bash
# Python バージョン確認
python3 --version

# 仮想環境を作成（カレントディレクトリに `.venv` が作られます）
python3 -m venv .venv

# 仮想環境を有効化（zsh）
source .venv/bin/activate
```

2) pip の更新と依存インストール

```bash
# pip をアップデート
python -m pip install --upgrade pip setuptools wheel

# Flask アプリの依存をインストール
python -m pip install -r web_app/requirements.txt
```

3) 開発サーバ起動

```bash
# 開発用（デバッグモード）
python3 web_app/app.py
```

サーバはデフォルトで `http://127.0.0.1:5000` で起動します。

4) 本番風に起動（gunicorn）

gunicorn をインストール済みであれば軽く本番風に起動できます（ポート8000例）。

```bash
gunicorn -w 4 -b 127.0.0.1:8000 web_app.app:app
```

5) 動作確認（推奨ページ）
- Home: `http://127.0.0.1:5000/`
- Goods: `http://127.0.0.1:5000/goods`
- Product: `http://127.0.0.1:5000/product/APP-001`
- Checkout: `http://127.0.0.1:5000/checkout`
- Admin orders: `http://127.0.0.1:5000/admin/orders`

初回起動時に `web_app/app.db`（SQLite）が作成され、`products` テーブルに要件の10商品が自動でシードされます。

6) テスト用の支払いシミュレーション

- 注文確定後に表示される支払いコード画面で「支払いをシミュレート」を押すか、以下のAPIを叩いて支払い完了状態にできます（開発用）。

```bash
curl -X POST -H "Content-Type: application/json" -d '{"code":"PCXXXXXXXXXX"}' http://127.0.0.1:5000/api/payments/simulate
```

（実際のコードは注文後にレスポンスで受け取る `payment_code` を使ってください）

よくあるトラブルと対処
- `venv` 作成に失敗する／permission エラー: Python のインストールを確認、またはディレクトリの書き込み権限を確認してください。
- pip インストールでビルドエラー: Xcode CLI tools が必要な場合があります。`xcode-select --install` を実行してください。
- ポートが既に使用中: `lsof -i :5000` 等でプロセスを確認し、停止するか別ポートで起動してください。
- `web_app/app.py` 実行時に AttributeError / RuntimeError が出る場合: 以前の環境で Flask のバージョン差分が原因のことがあります。`web_app/requirements.txt` を使ってクリーンな仮想環境を作り直してください。

追加の作業候補
- カートページ（`/cart`）のテンプレート追加／UI調整
- 支払いコードのQR画像生成とメール送信（SMTP）
- 認証（管理画面・ユーザページ）とCSRF対策
- 自動テスト（E2E）スクリプトの追加

サポート
実行中にエラーが出たら、ターミナルのエラーログ（フルスタックトレース）をここに貼ってください。解析して対処方法を提示します。

---
作成者: 開発補助スクリプト
