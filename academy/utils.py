# academy/utils.py
import re
from typing import List
from datetime import datetime
from zoneinfo import ZoneInfo
from datetime import date

import pandas as pd

from .config import (
    COL_ID, COL_NAME, COL_SCHOOL, COL_GRADE,
    WEEKDAY_ORDER
)

RE_SPACES = re.compile(r"\s+")
RE_DIGITS = re.compile(r"\d+")

KST = ZoneInfo("Asia/Seoul")

def now_kst() -> datetime:
    return datetime.now(KST)

def today_kst() -> date:
    return now_kst().date()

def norm(v) -> str:
    """단일 값(셀) 정규화: NBSP/전각공백/모든 공백 제거"""
    if v is None:
        return ""
    # pandas NaN 대응
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass

    s = str(v).replace("\u00A0", "").replace("\u3000", "")
    return RE_SPACES.sub("", s)


def split_days(days_str: str) -> List[str]:
    """'월,수' -> ['월','수'] (공백 제거 포함)"""
    s = norm(days_str)
    return [x for x in s.split(",") if x]


def periods_has_day_markers(periods_str: str) -> bool:
    """'월1,수2'처럼 요일 마커 포함 여부"""
    s = norm(periods_str)
    return any(d in s for d in WEEKDAY_ORDER)


def extract_period_numbers(periods_str: str) -> List[int]:
    """'1,2,3' / '1 2 3' / '1/2/3' 등에서 숫자만 추출"""
    s = norm(periods_str)
    nums = RE_DIGITS.findall(s)
    out: List[int] = []
    for n in nums:
        try:
            v = int(n)
            if v > 0:
                out.append(v)
        except Exception:
            pass
    return out


def match_attendance(days_str, periods_str, target_day, target_period) -> bool:
    """
    (테이블2에서 사용) 요일/교시 매칭.
    - days: '월,수'
    - periods:
      * 마커 있음: '월1,수2' (콤마 토큰 기준)
      * 숫자만: '1,2,3'
    """
    days = split_days(days_str)
    if target_day not in days:
        return False

    pstr = norm(periods_str)
    if not pstr:
        return False

    if periods_has_day_markers(pstr):
        return f"{target_day}{target_period}" in [x for x in pstr.split(",") if x]
    return str(target_period) in [str(n) for n in extract_period_numbers(pstr)]


def format_student_name(name, school, grade, pause_mark=""):
    s_str, g_str = str(school).strip(), str(grade).strip()
    school_grade = s_str + (g_str[1:] if s_str and g_str and s_str[-1] == g_str[0] else g_str)
    return f"{name}({school_grade}){pause_mark}"


def get_student_key(row: pd.Series) -> str:
    """배정 저장용 고유키: 학생ID 우선, 없으면 (이름|학교|학년)"""
    sid = str(row.get(COL_ID, "")).strip()
    if sid and sid.lower() != "nan":
        return f"id:{sid}"

    name = str(row.get(COL_NAME, "")).strip()
    school = str(row.get(COL_SCHOOL, "")).strip()
    grade = str(row.get(COL_GRADE, "")).strip()
    return f"ng:{name}|{school}|{grade}"


def sanitize_letter(v: str) -> str:
    """A~Z 한 글자만 허용"""
    s = str(v).strip().upper()
    if not s:
        return ""
    ch = s[0]
    return ch if ("A" <= ch <= "Z") else ""