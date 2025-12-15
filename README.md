# lecturedb データベーススキーマ

## courses テーブル
| カラム名         | 型      | 説明                       |
|------------------|---------|----------------------------|
| id               | INTEGER | 主キー（自動採番）         |
| category         | TEXT    | 区分（教養/専門など）      |
| code             | TEXT    | 科目番号                   |
| title            | TEXT    | 授業科目名                 |
| credits          | TEXT    | 単位数                     |
| grade            | TEXT    | 標準履修年次               |
| required_or_choice | TEXT  | 必修・選択                 |
| semester         | TEXT    | 実施学期                   |
| description      | TEXT    | 授業概要                   |
| note             | TEXT    | 備考                       |
| sheet_name       | TEXT    | 元Excelシート名            |

## course_times テーブル
| カラム名   | 型      | 説明               |
|------------|---------|--------------------|
| id         | INTEGER | 主キー（自動採番） |
| course_id  | INTEGER | courses.idへの外部キー |
| day        | TEXT    | 曜日               |
| period     | TEXT    | 時限               |
| room       | TEXT    | 教室               |
| remarks    | TEXT    | 備考・特記事項     |

## course_instructors テーブル
| カラム名   | 型      | 説明               |
|------------|---------|--------------------|
| id         | INTEGER | 主キー（自動採番） |
| course_id  | INTEGER | courses.idへの外部キー |
| instructor | TEXT    | 担当教員名         |

---

## 備考
- SQLite3形式
- Excelの各シートごとに`sheet_name`で区別
- 担当教員は複数名対応
- 時間割（曜日・時限・教室）は複数対応

## 前処理
- 全てのシートはヘッダーが６行目になるようにしてください
- 全てのシートは区分がA列になるようにしてください

## 実行方法

1. 必要なライブラリをインストール

```sh
pip install pandas openpyxl
```

2. スクリプトを実行

Excelファイル名を指定（省略時は「授業概要.xlsx」）

```sh
python3 main.py [Excelファイル名.xlsx]
```

例:
```sh
python3 main.py sample.xlsx
```

実行後、`courses.db` というSQLiteデータベースが生成されます。

**今回追加したリレーション（卒業要件関連）**

- **departments:** 学科・コース・領域を表すテーブル。
	- **columns:** `id` (INTEGER PK), `department_name` (TEXT, 学科名), `program_name` (TEXT, コース名), `domain_name` (TEXT, 領域名)

- **course_categories:** 科目区分（大区分・中区分・教養選択フラグ）を表すテーブル。
	- **columns:** `id` (INTEGER PK), `major_category` (TEXT, 大区分), `middle_category` (TEXT, 中区分), `is_liberal_elective` (INTEGER, 教養選択フラグ 0/1)

- **requirements:** 学科（専攻）×科目区分ごとの卒業要件（必要単位・必修/選択・適用年度）を表すテーブル。
	- **columns:** `id` (INTEGER PK), `department_id` (INTEGER FK→departments.id), `course_category_id` (INTEGER FK→course_categories.id),
		`required_credits` (INTEGER, 必要単位), `requirement_type` (TEXT, 'required' or 'elective'), `start_year` (INTEGER), `end_year` (INTEGER or NULL)

**CSVインポート（data フォルダ）**
- CSV ファイルは `data/` に配置しています: `departments.csv`, `course_categories.csv`, `requirements.csv`。
- SQLite CLI を使う場合の手順（ヘッダ行がある場合はヘッダを削除するか、`.import --skip 1` をサポートする sqlite3 を使ってください）:

```sh
cd /Users/chiemi/works/campushackers/courses-database/data
sqlite3 ../courses.db < requirements.sql

# もしくは対話モードでヘッダ有りのCSVをインポートする場合
sqlite3 ../courses.db
.mode csv
.import --skip 1 departments.csv departments
.import --skip 1 course_categories.csv course_categories
.import --skip 1 requirements.csv requirements
```

**備考**
- `requirements.sql` は SQLite 用に調整済みで、テーブル作成から `.import` までの手順を含みます。
- `requirement_type` は現在 `'required'` / `'elective'` のいずれかを想定しています。CSV の値が日本語の場合は事前にマッピングしてください。
