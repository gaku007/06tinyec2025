# req.md

概要
- 本ドキュメントは、アイドルグッズを扱う EC サイト（約10画面想定）の要件定義書。決済は「自社発行コード」によるコンビニ店頭支払い＋店舗受取（身分証確認）方式を含む。初期カタログはイベント3件×各20商品を想定。

対象ユーザ／ユースケース
- 個人のファンを想定（モバイル優先）。イベントごとの限定グッズを購入し、近隣のコンビニで支払って受け取る利用を想定。

画面一覧（UI要件）
- Home（ホーム）: ヒーローバナー、注目イベント、おすすめ商品カルーセル、カテゴリショートカット。
- Category / Listing（商品一覧）: サムネイル、価格、在庫表示、並べ替え、絞り込み（イベント/価格/属性）。
- Product Detail（商品詳細）: 画像ギャラリー、説明、価格、在庫、数量選択、カート追加、レビュー。
- Search（検索結果）: キーワード検索とファセット絞り込み、結果数表示。
- Cart（カート）: 商品一覧、数量変更、クーポン入力、配送/受取方法選択（コンビニ受取選択可）。
- Checkout（チェックアウト）: ログイン/ゲスト選択、支払方法選択（コンビニ支払を含む）、受取店舗選択、最終確認。
- Payment Code Display（支払いコード表示）: 自社発行コード、支払い期限、支払い手順（店頭提示用）、印刷/画面提示ボタン。
- Order Confirmation（注文完了）: 注文番号、明細、受取方法・店舗情報、支払期限通知、確認メール案内。
- Account / My Page（マイページ）: 注文履歴、住所帳、身分証登録（受取時用に任意で事前アップロード可）。
- Admin Dashboard（管理者）: 商品管理、在庫管理、注文一覧（支払状況・受取状況）、コード発行ログ、売上レポート。
- Help / Policies（ヘルプ・法務）: 返品ポリシー、特定商取引法に基づく表示、FAQ、受取時の身分証案内。

データモデル（主要エンティティ）
- User: id, email, password_hash, name, phone, created_at, is_admin
- Product: id, sku, name, description, price, currency, tax_included(bool), stock, event_id, images[], attributes[]
- Event: id, name, start_date, end_date, description, slug
- Category: id, name, parent_id, slug
- CartItem: id, user_id(nullable), product_id, quantity, created_at
- Order: id, user_id(nullable), status(pending/paid/cancelled/fulfilled), total_amount, shipping_fee, tax_amount, payment_method, payment_status, payment_code, payment_deadline, pickup_store_id, created_at
- OrderItem: id, order_id, product_id, quantity, unit_price, subtotal
- PaymentCode: id, order_id, code, issued_at, expires_at, status(unpaid/paid/expired/void), issued_by(system/admin)
- PickupLocation (Store): id, chain_name(Seven/LAWSON/FamilyMart), store_code, name, address, phone, latitude, longitude
- PaymentTransaction: id, order_id, payment_provider, transaction_id, amount, paid_at, raw_payload
- IdentityVerificationRecord: id, order_id, verifier_name, id_type, id_number_hash, verified_at, notes
- InventoryTransaction: id, product_id, change, reason(reservation/sale/cancel), created_at

API（想定エンドポイント）
- 商品関連: GET /api/products, GET /api/products/{id}, GET /api/events, GET /api/events/{id}
- カート: GET /api/cart, POST /api/cart (product_id, qty), PUT /api/cart/items/{id}, DELETE /api/cart/items/{id}
- 注文/チェックアウト: POST /api/checkout (cart, user/guest info, pickup_store_id, payment_method), GET /api/orders/{id}, GET /api/orders (user)
- 支払いコード管理: POST /api/payments/code (order_id) — コード発行（自社で生成）
- 支払い状態確認: GET /api/payments/code/{code} — コードステータス取得
- 支払い通知(Webhook): POST /api/payments/webhook — 店舗/決済プロバイダ経由の支払通知（受信・照合用）
- 受取確認: POST /api/orders/{id}/pickup/confirm — 店舗または管理者による受取確認（身分証確認フラグ）
- 管理者用: GET/POST/PUT/DELETE /api/admin/products, /api/admin/orders, /api/admin/payment-codes
- 補助: GET /api/health, GET /api/config (公開設定: 受取可能チェーンなど)

ユーザーフロー（主要）
- 通常購入（コンビニ受取を含む）
  1. ユーザは商品を選びカートへ追加。
  2. チェックアウトで「受取方法：コンビニ」を選択し、受取チェーン（セブンイレブン / ローソン / ファミリーマート）と来店店舗を指定。
  3. 注文作成時にシステムは在庫を72時間確保（Reservation）。同時に自社発行の支払いコードを生成し、支払い有効期限（3日）を設定。
  4. 支払いコード表示画面／メールでコードと支払期限を通知（印刷ボタンと店頭提示用QRを表示）。
  5. 購入者は指定のコンビニへ行き、店頭レジでコードと代金を支払う（現金・店側の支払手続き）。
  6. 店舗または決済プロバイダから当システムへ支払完了通知が届き、PaymentCode.status を paid に更新し Order.status を paid に遷移。
  7. 指定した店舗で身分証（運転免許証／マイナンバーカード／パスポートのいずれか）を提示し、店舗側が IdentityVerificationRecord を記録して商品を引渡し。Order.status を fulfilled に更新。
  8. 受取確認・レビュー誘導のメール送付。未払いのまま有効期限超過 → 自動キャンセル・在庫戻し処理（72時間の予約と3日の支払期限を考慮）。

- 返金・返品（概要）
  - 返品は受取後の状態に応じて対応。支払いが店頭完結しているため、返金は原則として銀行振込か別途決済処理により対応。管理者フローで返品受付・返金処理を行う。

非機能要件（要点）
- 在庫ポリシー: コード発行時に72時間在庫を確保。未払いの場合は自動キャンセルで在庫戻し。
- 支払い有効期間: コード発行から「3日間（72時間）」を標準とする。
- 可用性: 99.9% 目標（ロードバランサ・冗長化）。
- パフォーマンス: API 95パーセンタイル < 300ms。静的資産は CDN 配信。
- セキュリティ: HTTPS 必須、CSRF/XSS 保護、パスワードは bcrypt/argon2、個人情報は暗号化保存、ログアクセス制御。
- 監視: エラーログ・重要指標（未払い率、支払成功率、受取成功率）をアラート設定。
- アクセシビリティ: WCAG AA 準拠を目指す。

支払い・コンビニ連携の運用注意
- 対応チェーン: セブンイレブン / ローソン / ファミリーマート をサポート。これらのチェーンで店頭支払いを受け付けるため、通常は各チェーンに対応した決済プロバイダ（PSP）またはコンビニ収納代行サービスとの契約が必要。自社発行コードを用いる場合でも、店舗での支払受付と売上入金の取り扱いをどう行うか（プロバイダ経由での入金・与信／店との取り決め）を決める必要あり。
- コード仕様（自社発行）: システム側でユニークコードを生成（例: 英数字12桁 + チェックサム）。発行ログと有効期限を保存し、店舗側照合プロセス（レジ入力による照合）との運用フローを定義する。
- 店舗側での受取認証: 受取時に必須の身分証は「運転免許証、マイナンバーカード、パスポート」のいずれか。店舗スタッフは注文に紐づく氏名と提示IDの氏名・顔写真を確認し、照合した旨をシステムに記録する。本人確認ログは法令遵守とトラブル対応のため保存。
- 決済通知: 店舗または PSP からの支払完了通知（Webhook）を受け、決済トランザクションと照合する仕組みを用意する。
- 返金対応: 店頭での支払い完了後の返品では、返金は管理者経由（銀行振込等）で行う運用が現実的。返金ポリシーを明文化する。

初期カタログ（サンプル）
- イベントA（Event-A）: 価格は概念値、在庫は初期在庫例
  1. EVT-A-001 | Tシャツ（白） | ¥3,500 | stock 50
  2. EVT-A-002 | Tシャツ（黒） | ¥3,500 | stock 50
  3. EVT-A-003 | タオル（ロゴ） | ¥1,500 | stock 100
  4. EVT-A-004 | トレカセット（10枚） | ¥2,000 | stock 200
  5. EVT-A-005 | ポスターA2 | ¥1,200 | stock 80
  6. EVT-A-006 | 缶バッジ（ランダム） | ¥500 | stock 300
  7. EVT-A-007 | アクリルスタンド | ¥1,800 | stock 70
  8. EVT-A-008 | ステッカーセット | ¥700 | stock 150
  9. EVT-A-009 | フォトブック | ¥2,500 | stock 60
  10. EVT-A-010 | ネックレス（会場限定） | ¥4,000 | stock 30
  11. EVT-A-011 | キャップ | ¥2,200 | stock 40
  12. EVT-A-012 | エコバッグ | ¥1,000 | stock 120
  13. EVT-A-013 | ブロマイド（全員セット） | ¥2,200 | stock 90
  14. EVT-A-014 | スマホリング | ¥1,100 | stock 85
  15. EVT-A-015 | マフラータオル（限定色） | ¥2,000 | stock 50
  16. EVT-A-016 | ラバーブレスレット | ¥800 | stock 180
  17. EVT-A-017 | クリアファイルセット | ¥900 | stock 140
  18. EVT-A-018 | 限定CD | ¥2,800 | stock 40
  19. EVT-A-019 | ライブ写真セット | ¥1,600 | stock 75
  20. EVT-A-020 | ミニライト | ¥2,300 | stock 65

- イベントB（Event-B）
  1. EVT-B-001 | Tシャツ（白） | ¥3,500 | stock 50
  2. EVT-B-002 | Tシャツ（黒） | ¥3,500 | stock 50
  3. EVT-B-003 | タオル（ロゴ） | ¥1,500 | stock 100
  4. EVT-B-004 | トレカセット（10枚） | ¥2,000 | stock 200
  5. EVT-B-005 | ポスターA2 | ¥1,200 | stock 80
  6. EVT-B-006 | 缶バッジ（ランダム） | ¥500 | stock 300
  7. EVT-B-007 | アクリルスタンド | ¥1,800 | stock 70
  8. EVT-B-008 | ステッカーセット | ¥700 | stock 150
  9. EVT-B-009 | フォトブック | ¥2,500 | stock 60
  10. EVT-B-010 | ネックレス（会場限定） | ¥4,000 | stock 30
  11. EVT-B-011 | キャップ | ¥2,200 | stock 40
  12. EVT-B-012 | エコバッグ | ¥1,000 | stock 120
  13. EVT-B-013 | ブロマイド（全員セット） | ¥2,200 | stock 90
  14. EVT-B-014 | スマホリング | ¥1,100 | stock 85
  15. EVT-B-015 | マフラータオル（限定色） | ¥2,000 | stock 50
  16. EVT-B-016 | ラバーブレスレット | ¥800 | stock 180
  17. EVT-B-017 | クリアファイルセット | ¥900 | stock 140
  18. EVT-B-018 | 限定CD | ¥2,800 | stock 40
  19. EVT-B-019 | ライブ写真セット | ¥1,600 | stock 75
  20. EVT-B-020 | ミニライト | ¥2,300 | stock 65

- イベントC（Event-C）
  1. EVT-C-001 | Tシャツ（白） | ¥3,500 | stock 50
  2. EVT-C-002 | Tシャツ（黒） | ¥3,500 | stock 50
  3. EVT-C-003 | タオル（ロゴ） | ¥1,500 | stock 100
  4. EVT-C-004 | トレカセット（10枚） | ¥2,000 | stock 200
  5. EVT-C-005 | ポスターA2 | ¥1,200 | stock 80
  6. EVT-C-006 | 缶バッジ（ランダム） | ¥500 | stock 300
  7. EVT-C-007 | アクリルスタンド | ¥1,800 | stock 70
  8. EVT-C-008 | ステッカーセット | ¥700 | stock 150
  9. EVT-C-009 | フォトブック | ¥2,500 | stock 60
  10. EVT-C-010 | ネックレス（会場限定） | ¥4,000 | stock 30
  11. EVT-C-011 | キャップ | ¥2,200 | stock 40
  12. EVT-C-012 | エコバッグ | ¥1,000 | stock 120
  13. EVT-C-013 | ブロマイド（全員セット） | ¥2,200 | stock 90
  14. EVT-C-014 | スマホリング | ¥1,100 | stock 85
  15. EVT-C-015 | マフラータオル（限定色） | ¥2,000 | stock 50
  16. EVT-C-016 | ラバーブレスレット | ¥800 | stock 180
  17. EVT-C-017 | クリアファイルセット | ¥900 | stock 140
  18. EVT-C-018 | 限定CD | ¥2,800 | stock 40
  19. EVT-C-019 | ライブ写真セット | ¥1,600 | stock 75
  20. EVT-C-020 | ミニライト | ¥2,300 | stock 65

インテグレーション（外部連携）
- コンビニ連携: 各チェーンの店頭支払いを取り扱う PSP/収納代行業者との契約を推奨。自社コードの店舗照合フローや、支払通知を受ける Webhook 設計が必要。
- 通知: メール・SMS 配信（支払期限リマインド用）。
- ログ/監視: 中央ログ（例: ELK/Datadog）、支払イベントの監査ログ保存。

運用／法務要件
- 特定商取引法に基づく表示をサイト上に明示（事業者名、住所、代表連絡先、販売価格、送料、支払時期、返品条件）。
- 個人情報保護: 受取時身分証の取扱い（撮影保存する場合は法的助言を得て、保存・破棄ポリシーを明記）。ID番号そのものは保存しない、もしくはハッシュ化して保存する方針を推奨。
- 返品・返金ポリシーを明確化（店頭支払いの返品時の返金方法を明示）。

リスクと未解決事項
- 自社発行コードでの運用は店舗側レジとの運用調整が必要（人為ミス・照合遅延のリスク）。
- 決済プロバイダ選定（PSP 経由にするか完全自社処理にするか）— 法務・会計・手数料面の検討要。
- 身分証提示に関する個人情報保護の扱い（撮影保存の可否／ログ保持期間）は法務確認必須。

ローンチ（MVP）提案
- フェーズ1（MVP）: イベント1つ分（20商品）、コンビニはまず1チェーン（例: ローソン）で稼働、コード発行→店頭支払い→受取の一連フローを検証。支払い有効期間は3日、在庫予約72時間。
- フェーズ2: 全チェーン対応、イベントを3つ（60商品）に拡張、管理ダッシュボード機能強化、返品フロー確立。
- フェーズ3: 検索強化（Algolia/Elasticsearch）、多決済対応、国際販売検討。

付録（運用パラメータ）
- 在庫予約期間: 72時間（自動キャンセル時に在庫を戻す）。
- 支払い有効期間: 3日（発行時刻から72時間有効）。
- 受取時身分証: 運転免許証、マイナンバーカード、パスポート（いずれか必須）。

---
作成者: 自動生成ドラフト
次のアクション: レビュー担当者を決め、フィードバックを受けて `req.md` を更新する。
