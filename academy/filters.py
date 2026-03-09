# academy/filters.py
import re
import pandas as pd

from .config import COL_DAYS, COL_PERIOD, WEEKDAY_ORDER


def norm_series(sr: pd.Series) -> pd.Series:
    """Series 전용 정규화: NaN -> '', 공백 및 기호(/)를 콤마(,)로 통일!"""
    return (
        sr.fillna("")
          .astype(str)
          .str.replace("\u00A0", " ", regex=False)  # 특수공백을 일단 일반공백으로
          .str.replace("\u3000", " ", regex=False)  # 전각공백도 일반공백으로
          # ✨ 핵심: 모든 공백류(\s)와 슬래시(/)를 콤마(,)로 통일!
          .str.replace(r"[\s/]+", ",", regex=True)
          # ✨ 혹시 "월1, 수2" 처럼 쳐서 ",,"가 된 경우를 위해 콤마 1개로 압축
          .str.replace(r",+", ",", regex=True)
          # 양끝에 남은 콤마 제거
          .str.strip(",")
    )


def filter_students_for_day_period(df: pd.DataFrame, weekday: str, period: int) -> pd.DataFrame:
    """
    df에서 weekday에 등원하고, period에 해당하는 학생만 필터링해 반환.
    - COL_DAYS: "월,수" 형태
    - COL_PERIOD:
        * 요일마커 있음: "월1,수2" → 해당 weekday+period 토큰 포함
        * 숫자만 있음: "1,2,3" / "1 2 3" / "1/2/3" 등 → period 숫자 포함
    """
    if df is None or df.empty:
        return df.copy() if df is not None else pd.DataFrame()

    days = norm_series(df[COL_DAYS])
    pstr = norm_series(df[COL_PERIOD])

    # 요일 포함 여부: (^|,)월(,|$)
    day_pat = rf"(?:^|,){re.escape(weekday)}(?:,|$)"
    mask_day = days.str.contains(day_pat, regex=True, na=False)

    # 요일 마커 포함 여부
    marker_pat = "(?:" + "|".join(map(re.escape, WEEKDAY_ORDER)) + ")"
    has_marker = pstr.str.contains(marker_pat, regex=True, na=False)

    # 마커가 있는 경우: (^|,)월1(,|$)
    token_pat = rf"(?:^|,){re.escape(weekday)}{int(period)}(?:,|$)"
    mask_marker = pstr.str.contains(token_pat, regex=True, na=False)

    # 숫자만 있는 경우: 1이 10/11에 매칭되면 안 됨
    num_pat = rf"(?<!\d){int(period)}(?!\d)"
    mask_numeric = pstr.str.contains(num_pat, regex=True, na=False)

    mask = mask_day & ((has_marker & mask_marker) | ((~has_marker) & mask_numeric))
    return df.loc[mask].copy()