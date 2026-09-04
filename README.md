# danbooru-tag-categories-ja

Danbooruのタグ名、日本語訳、カテゴリをまとめた辞書です。タグ検索や画像生成用のプロンプト作成に使えます。

## ファイル

- `index.csv`: タグ辞書本体。現在19,525件
- `data/appearance_tag_additions.csv`: 新しく追加したタグ196件の一覧。投稿数と作成日も記録
- `data/manual_audit_corrections.csv`: 目視監査で修正した321件の一覧。修正前後の訳・カテゴリと理由を記録
- `scripts/tag_classification.py`: タグのカテゴリ分類ルール
- `scripts/refine_index.py`: CSVの再分類、追加タグの登録、修正台帳の適用を行うスクリプト
- `tests/`: 分類ルールと更新処理のテスト

## CSVの列

- `index`: 通し番号
- `tag`: Danbooruタグ
- `db_category_filled`: 元データのカテゴリ
- `tag_jp`: 日本語名
- `category_jp`: 日本語カテゴリ

## 分類

髪・目・肌を分けて分類しています。

- `髪`: 頭髪の色、長さ、前髪、髪型、質感など
- `目`: 目の色、虹彩、瞳孔、強膜、眉、まつげなど
- `肌`: 肌の色、そばかす、日焼け、ほくろ、傷跡など

表情、視線、動作、状態、アクセサリー、化粧、効果・演出、作品関係などは、それぞれのカテゴリに分けています。キャラクター名や作品名などの固有名詞も別カテゴリのままです。

## 追加タグ

Danbooru APIで確認したタグのうち、既存CSVにないタグを196件追加しています。追加台帳の確認時点での内訳は、髪101件、目73件、肌22件です。目視確認後、タグの意味に合わせて一部をアクセサリー、作品関係、状態、効果・演出などのカテゴリへ移しています。

## 目視修正

元の19,329件と追加196件を確認し、カテゴリの違い、誤訳、外見と状態・動作・効果の混同などを321件修正しました。修正内容は`data/manual_audit_corrections.csv`にまとめています。

## 再生成

リポジトリのルートで次を実行すると、`index.csv`を再生成できます。

```bash
python scripts/refine_index.py \
  --input index.csv \
  --additions data/appearance_tag_additions.csv \
  --corrections data/manual_audit_corrections.csv \
  --output index.csv
```

## テスト

```bash
python -m unittest discover -s tests -v
```

## 注意

このデータには、Danbooruタグ由来の一部NSFWな単語が含まれます。
