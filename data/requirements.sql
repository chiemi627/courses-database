-- ...existing code...

PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

DROP TABLE IF EXISTS requirements;
DROP TABLE IF EXISTS course_categories;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  department_name TEXT NOT NULL,   -- 学科名
  program_name TEXT,               -- コース名
  domain_name TEXT                 -- 領域名
);

CREATE TABLE course_categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  major_category TEXT,             -- 大区分
  middle_category TEXT,            -- 中区分
  is_liberal_elective INTEGER DEFAULT 0 -- 教養選択フラグ (0/1)
);

CREATE TABLE requirements (
  id INTEGER PRIMARY KEY,
  course_category_id INTEGER NOT NULL,
  department_id INTEGER NOT NULL,
  required_credits INTEGER NOT NULL,
  requirement_type TEXT NOT NULL,
  start_year INTEGER NOT NULL,
  end_year INTEGER,
  FOREIGN KEY(department_id) REFERENCES departments(id) ON DELETE CASCADE,
  FOREIGN KEY(course_category_id) REFERENCES course_categories(id) ON DELETE CASCADE
);

CREATE INDEX idx_requirements_dept ON requirements(department_id);
CREATE INDEX idx_requirements_cat ON requirements(course_category_id);
CREATE INDEX idx_requirements_year ON requirements(start_year, end_year);

COMMIT;
PRAGMA foreign_keys = ON;

.mode csv
.import departments.csv departments 
.import course_categories.csv course_categories 
.import requirements.csv requirements 
