import pandas as pd
import sqlite3
import re
import unicodedata

INPUT_EXCEL = "授業概要.xlsx"   # ← 自分のファイル名に合わせて変更

# ==========
# 2. 曜日・時限の解析ロジック
# ==========

WEEKDAYS = "月火水木金土日"

def parse_day_period(line):
    """
    曜日 + 時限をパースして (day, period) のリストを返す。
    例：
    月3 → [(月, 3)]
    木4.5 → [(木,4),(木,5)]
    金2・3 → 同上
    月34 → [(月,3),(月,4)]
    金2-4 → [(金,2),(金,3),(金,4)]
    """
    def to_hankaku(s):
        return unicodedata.normalize('NFKC', s)
    if not isinstance(line, str):
        return None
    line = line.strip()
    if not line or line[0] not in WEEKDAYS:
        return None
    day = to_hankaku(line[0])
    rest = to_hankaku(line[1:])
    rest = rest.replace('．','.') \
               .replace('・','.') \
               .replace('･','.')
    # 範囲指定（3-5）
    if '-' in rest:
        parts = rest.split('-')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            s, e = int(parts[0]), int(parts[1])
            return [(day, to_hankaku(str(p))) for p in range(s, e+1)]
        return None
    # 区切り記号（4.5）
    if '.' in rest:
        toks = rest.split('.')
        periods = [int(t) for t in toks if t.isdigit()]
        return [(day, to_hankaku(str(p))) for p in periods] if periods else None
    # 例：34 → 3,4
    if rest.isdigit() and len(rest) >= 2:
        return [(day, to_hankaku(ch)) for ch in rest]
    # 単一（4）
    if rest.isdigit():
        return [(day, to_hankaku(rest))]
    return None


def parse_special(line):
    """特別ワード（集中 / 隔週 / 指導教員 / 1学期 / 2学期）"""
    if not isinstance(line, str):
        return None
    specials = ["集中", "隔週", "指導教員", "1学期", "2学期", "指導教員の指示による"]
    for s in specials:
        if s in line:
            return s
    return None


def parse_room(line):
    """教室情報（201, 202, 509, 工房, プレゼンルーム, 113他）"""
    def to_hankaku(s):
        return unicodedata.normalize('NFKC', s)
    if not isinstance(line, str):
        return None, None
    line = line.strip()
    if not line:
        return None, None
    m = re.match(r"(\d+)(他)?", line)
    if m:
        return to_hankaku(m.group(1)), ("他" if m.group(2) else None)
    # 工房・プレゼンルーム・教室名
    known_rooms = ["工房", "プレゼンルーム"]
    if line in known_rooms:
        return to_hankaku(line), None
    return to_hankaku(line), None


def parse_cell(cell):
    """
    「曜時限＋教室」セル全体を解析して返す。
    返り値：[(day, period, room, remarks), ...]
    """
    results = []
    day_periods = []
    rooms = []
    remarks = []

    # 複数行のセルを行ごとに処理
    import unicodedata
    def to_hankaku(s):
        return unicodedata.normalize('NFKC', s)

    results = []
    last_day_periods = []
    remarks = []

    import re
    raw = str(cell)
    # 「曜日＋時限＋教室」パターンに該当する場合のみ分割
    # 例: 月3 316, 月４　３１６, 月3\n316 など
    # 曜日1文字＋数字が含まれていれば分割対象とみなす
    if re.search(r'[月火水木金土日][0-9０-９]', raw):
        # 改行・全角スペース・タブで分割
        split_pattern = r'[\n\u3000\t]+'
        lines = [to_hankaku(l.strip()) for l in re.split(split_pattern, raw) if l.strip()]
    else:
        # それ以外は従来通り1行として扱う
        lines = [to_hankaku(raw.strip())] if raw.strip() else []

    for line in lines:
        # 特殊ワード
        sp = parse_special(line)
        if sp:
            remarks.append(sp)
            continue

        # 曜日・時限
        dp = parse_day_period(line)
        if dp:
            last_day_periods = dp
            continue

        # 教室
        room, rem = parse_room(line)
        if room:
            # 直前の曜日・時限とペアにする
            if last_day_periods:
                for day, period in last_day_periods:
                    results.append((day, period, room, ", ".join(remarks) if remarks else None))
                last_day_periods = []
            else:
                results.append((None, None, room, ", ".join(remarks) if remarks else None))
            if rem:
                remarks.append(rem)
            continue

    # 残った曜日・時限だけ
    if last_day_periods:
        for day, period in last_day_periods:
            results.append((day, period, None, ", ".join(remarks) if remarks else None))

    # 何もなければremarksだけ
    if not results:
        results.append((None, None, None, ", ".join(remarks) if remarks else None))

    return results
# ==========

DB_PATH = "courses.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# テーブル作り直し
cur.executescript("""
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS course_times;
DROP TABLE IF EXISTS course_instructors;

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    code TEXT,
    title TEXT,
    credits TEXT,
    grade TEXT,
    required_or_choice TEXT,
    semester TEXT,
    description TEXT,
    note TEXT,
    sheet_name TEXT
);

CREATE TABLE course_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    day TEXT,
    period TEXT,
    room TEXT,
    remarks TEXT
);

CREATE TABLE course_instructors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    instructor TEXT
);
""")


# ==========
# データ挿入
# ==========

def insert_data(df):
    # print("[DEBUG] df.columns:", df.columns)
    for _, row in df.iterrows():
        if sheet_name=='1教養教育(産業情報)':
            print("[DEBUG] row:", row['区分'])
        # courses へ
        def safe_get(row, key):
            return str(row[key]) if key in row and not pd.isna(row[key]) else None

        # 実際のExcelカラム名に合わせてマッピング
        data = (
            safe_get(row, "区分"),
            safe_get(row, "科目\n番号"),
            safe_get(row, "授業科目"),
            safe_get(row, "単位数"),
            safe_get(row, "標準履修年次"),
            safe_get(row, "必修\n・\n選択"),
            safe_get(row, "実施学期"),
            safe_get(row, "授　　業　　概　　要"),
            safe_get(row, "　　備　考\n(対象専攻、教職免許\n の教科等)"),
            row.get("sheet_name")
        )

        c = cur.execute("""
            INSERT INTO courses (
                category, code, title, credits, grade,
                required_or_choice, semester, description, note, sheet_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        course_id = c.lastrowid

        # course_times へ（実際のカラム名で参照）
        time_entries = parse_cell(row.get("曜時限\n教  室", ""))
        for day, period, room, remarks in time_entries:
            cur.execute("""
                INSERT INTO course_times (course_id, day, period, room, remarks)
                VALUES (?, ?, ?, ?, ?)
            """, (course_id, day, period, room, remarks))

        # course_instructors へ（実際のカラム名で参照）
            insts = re.split(r"[,、，/・･\n]+", str(row.get("担当教員", "")))
            exclude_words = ['教員', '他', '情報', '建築', '機械', 'デザイン', '支援','コース','担当','全員']
            for inst in [i.strip() for i in insts if i.strip()]:
                inst_hankaku = unicodedata.normalize('NFKC', inst)
                # 日本人名らしさ判定（2文字以上、ひらがな・カタカナ・漢字のみ、指定ワード除外）
                if len(inst_hankaku) >= 2 and re.fullmatch(r'[ぁ-んァ-ヶ一-龥々ー]+', inst_hankaku):
                    if not any(word in inst_hankaku for word in exclude_words):
                        cur.execute("""
                            INSERT INTO course_instructors (course_id, instructor)
                            VALUES (?, ?)
                        """, (course_id, inst_hankaku))


# ==========
# Excel 読み込み
# ==========

sheets = pd.read_excel(INPUT_EXCEL, header=5, sheet_name=None)

for sheet_name, df in sheets.items():
    df = df.dropna(how="all")
    df = df.ffill()
    df["sheet_name"] = sheet_name
    print("[DEBUG] Processing sheet:", sheet_name)
    insert_data(df)

conn.commit()
conn.close()

print("🎉 SQLite データベース生成完了：", DB_PATH)