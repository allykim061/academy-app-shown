# academy/data.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from .config import (
    SCOPE, WORKSHEET_STUDENTS, WORKSHEET_STUDENTS_NEXT,
    REQUIRED_COLUMNS,
    COL_SCHOOL, COL_PERIOD, COL_STATUS, COL_DAYS,
    COL_STUDENT_MEMO,
)
from .utils import norm, normalize_school_name
from .filters import norm_series

@st.cache_data(ttl=300, show_spinner="loading...")
def load_data(worksheet_name: str = WORKSHEET_STUDENTS) -> pd.DataFrame:
    try:
        creds_info = st.secrets["SERVICE_ACCOUNT_INFO"]
        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPE)
        client = gspread.authorize(creds)

        sh = client.open(st.secrets["SPREADSHEET_NAME"])
        ws = sh.worksheet(worksheet_name)

        df = pd.DataFrame(ws.get_all_records())

        if df.empty:
            return df

        # 1) 컬럼명 정규화
        df.columns = [norm(c) for c in df.columns]

        # 2) 필수 컬럼 검증
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            st.error(f"구글 시트 헤더가 일치하지 않습니다. 누락된 항목: {missing}")
            st.info(f"현재 인식된 항목: {list(df.columns)}")
            st.stop()

        # 3) students 시트 공통 메모 컬럼 보장
        if COL_STUDENT_MEMO not in df.columns:
            df[COL_STUDENT_MEMO] = ""

        # 4) 주요 문자열 컬럼 정규화
        df[COL_SCHOOL] = df[COL_SCHOOL].apply(normalize_school_name)
        df[COL_PERIOD] = norm_series(df[COL_PERIOD])
        df[COL_DAYS] = norm_series(df[COL_DAYS])
        df[COL_STATUS] = df[COL_STATUS].astype(str).apply(norm)
        df[COL_STUDENT_MEMO] = df[COL_STUDENT_MEMO].fillna("").astype(str).str.strip()


        return df

    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()