# Reddit Buzz Tracker

See what retail investors are talking about — right now. Scans multiple subreddits, extracts stock tickers, and shows mention counts alongside live price data. Optional email report.

## Features

- Select from 6 major investing subreddits (r/wallstreetbets, r/stocks, r/investing, r/options, r/stockmarket, r/Superstonk)
- Extracts stock tickers from post titles and bodies
- Shows mention count, current price, and 1-day price change per ticker
- Links to the actual Reddit posts mentioning each stock
- Optional email summary report
- Clean web interface — no command line needed

## Setup

**1. Clone and install**

```bash
git clone https://github.com/xhqi01/reddit-buzz-tracker.git
cd reddit-buzz-tracker
pip install -r requirements.txt
```

**2. Get Reddit API credentials**

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **Create another app**
3. Choose type: **script**
4. Name it anything, redirect URI: `http://localhost`
5. Copy your `client_id` (under the app name) and `client_secret`

**3. Run the server**

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

Enter your Reddit credentials directly in the web UI — they are never stored.

## Deploy to Render (runs 24/7 for free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → **Web Service**
3. Connect your GitHub repo
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `python app.py`
6. Click Deploy

## Notes

- Stock data from Yahoo Finance (15-minute delay)
- Ticker extraction uses a curated list of known symbols + `$TICKER` pattern matching
- Not financial advice

---

# Reddit Buzz Tracker（日本語）

個人投資家が今何を話しているかをリアルタイムで把握するツールです。複数のサブレディットをスキャンし、銘柄の言及数とリアルタイム株価をあわせて表示します。

## 機能

- 6つの主要投資サブレディットから選択して監視
- 投稿タイトル・本文から銘柄ティッカーを自動抽出
- 言及数・現在株価・前日比を表示
- 各銘柄に言及しているReddit投稿へのリンク付き
- メールレポート送信オプション
- Webインターフェース — コマンドライン不要

## セットアップ

**1. クローンとインストール**

```bash
git clone https://github.com/xhqi01/reddit-buzz-tracker.git
cd reddit-buzz-tracker
pip install -r requirements.txt
```

**2. Reddit APIキーの取得**

1. [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) にアクセス
2. **Create another app** をクリック
3. タイプ: **script** を選択
4. 名前は何でもOK、redirect URI: `http://localhost`
5. `client_id`（アプリ名の下）と `client_secret` をコピー

**3. サーバーを起動**

```bash
python app.py
```

ブラウザで [http://localhost:5000](http://localhost:5000) を開く。

Reddit認証情報はWebUIで直接入力 — 保存されません。

## Renderへのデプロイ（24時間稼働・無料）

1. このリポジトリをGitHubにプッシュ
2. [render.com](https://render.com) → New → **Web Service**
3. GitHubリポジトリを接続
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `python app.py`
6. Deploy をクリック

## 注意事項

- 株価データはYahoo Finance（15分遅延）
- 投資アドバイスではありません
