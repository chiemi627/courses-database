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
