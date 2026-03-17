# academy/config.py

PAGE_TITLE = "학생 인원관리 시스템"

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

WORKSHEET_STUDENTS = "students"

COL_ID = "학생ID"
COL_NAME = "이름"
COL_SCHOOL = "학교"
COL_GRADE = "학년"
COL_DAYS = "등원요일"
COL_PERIOD = "수업교시"
COL_STATUS = "상태"
COL_STUDENT_MEMO = "메모"

REQUIRED_COLUMNS = {
    COL_ID, COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS, COL_STUDENT_MEMO
}

GRADE_ORDER = ["초1", "초2", "초3", "초4", "초5", "초6", "중1", "중2", "중3", "고1", "고2", "고3"]
WEEKDAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"]

WORKSHEET_ATTENDANCE_DATA = "attendance_data"
WORKSHEET_STUDENTS_MONTHLY_DATA = "students_monthly_data"

ATTENDANCE_BATCH_PREFIX = "att"
MONTHLY_BATCH_PREFIX = "monthly"

# attendance_data columns
COL_ATT_DATE = "날짜"
COL_ATT_PERIOD = "교시"
COL_ATT_STUDENT_KEY = "학생고유키"
COL_ATT_LETTER = "배정알파벳"
COL_ATT_ABSENT = "결석여부"
COL_ATT_UPDATED_AT = "수정시각"
COL_ATT_BATCH_ID = "저장배치ID"

ATTENDANCE_DATA_COLUMNS = [
    COL_ATT_DATE,
    COL_ATT_PERIOD,
    COL_ATT_STUDENT_KEY,
    COL_ATT_LETTER,
    COL_ATT_ABSENT,
    COL_ATT_UPDATED_AT,
    COL_ATT_BATCH_ID,
]

# students_monthly_data columns
COL_MONTHLY_MONTH = "기준월"
COL_MONTHLY_SAVED_AT = "저장일시"
COL_MONTHLY_BATCH_ID = "저장배치ID"

STUDENTS_MONTHLY_DATA_COLUMNS = [
    COL_MONTHLY_MONTH,
    COL_MONTHLY_SAVED_AT,
    COL_MONTHLY_BATCH_ID,
    COL_ID,
    COL_NAME,
    COL_SCHOOL,
    COL_GRADE,
    COL_DAYS,
    COL_PERIOD,
    COL_STATUS,
]

WORKSHEET_ATTENDANCE_TEACHER_NOTES = "attendance_teacher_notes"

COL_TNOTE_DATE = "날짜"
COL_TNOTE_PERIOD = "교시"
COL_TNOTE_NOTE = "담당메모"
COL_TNOTE_UPDATED_AT = "수정시각"

ATTENDANCE_TEACHER_NOTE_COLUMNS = [
    COL_TNOTE_DATE,
    COL_TNOTE_PERIOD,
    COL_TNOTE_NOTE,
    COL_TNOTE_UPDATED_AT,
]

WORKSHEET_WEEKLY_PERIOD_NOTES = "weekly_period_notes"

COL_WPN_PERIOD = "교시"
COL_WPN_NOTE = "비고"
COL_WPN_UPDATED_AT = "수정시각"

WEEKLY_PERIOD_NOTE_COLUMNS = [
    COL_WPN_PERIOD,
    COL_WPN_NOTE,
    COL_WPN_UPDATED_AT,
]