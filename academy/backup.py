# academy/backup.py
from __future__ import annotations

from typing import Dict, Tuple, Any
from uuid import uuid4

import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

from .config import (
    SCOPE,
    WORKSHEET_ATTENDANCE_DATA,
    WORKSHEET_STUDENTS_MONTHLY_DATA,
    WORKSHEET_ATTENDANCE_TEACHER_NOTES,
    ATTENDANCE_DATA_COLUMNS,
    STUDENTS_MONTHLY_DATA_COLUMNS,
    ATTENDANCE_TEACHER_NOTE_COLUMNS,
    ATTENDANCE_BATCH_PREFIX,
    MONTHLY_BATCH_PREFIX,
    COL_ATT_DATE,
    COL_ATT_PERIOD,
    COL_ATT_STUDENT_KEY,
    COL_ATT_LETTER,
    COL_ATT_ABSENT,
    COL_ATT_UPDATED_AT,
    COL_ATT_BATCH_ID,
    COL_MONTHLY_MONTH,
    COL_MONTHLY_SAVED_AT,
    COL_MONTHLY_BATCH_ID,
    COL_TNOTE_DATE,
    COL_TNOTE_PERIOD,
    COL_TNOTE_NOTE,
    COL_TNOTE_UPDATED_AT,
    COL_ID,
    COL_NAME,
    COL_SCHOOL,
    COL_GRADE,
    COL_DAYS,
    COL_PERIOD,
    COL_STATUS,
    WORKSHEET_WEEKLY_PERIOD_NOTES,
    COL_WPN_SOURCE,
    COL_WPN_PERIOD,
    COL_WPN_NOTE,
    COL_WPN_UPDATED_AT,
    WEEKLY_PERIOD_NOTE_COLUMNS,
)
from .utils import now_kst, sanitize_letter

DayStore = Dict[Tuple[int, str], Dict[str, Any]]


def _get_client():
    creds_info = st.secrets["SERVICE_ACCOUNT_INFO"]
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPE)
    return gspread.authorize(creds)


def _get_spreadsheet():
    client = _get_client()
    return client.open(st.secrets["SPREADSHEET_NAME"])


def _get_or_create_worksheet(sh, title: str, headers: list[str]):
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=max(len(headers), 10))
        ws.append_row(headers)

    current_headers = ws.row_values(1)
    if current_headers != headers:
        if not current_headers:
            ws.append_row(headers)
        else:
            raise ValueError(
                f"워크시트 '{title}' 헤더가 예상과 다릅니다.\n"
                f"현재: {current_headers}\n예상: {headers}"
            )
    return ws


def _new_batch_id(prefix: str) -> str:
    ts = now_kst().strftime("%Y%m%d%H%M%S")
    short_uuid = uuid4().hex[:8]
    return f"{prefix}_{ts}_{short_uuid}"


def serialize_day_store(date_key: str, day_store: DayStore, batch_id: str) -> list[list[Any]]:
    updated_at = now_kst().strftime("%Y-%m-%d %H:%M:%S")
    rows: list[list[Any]] = []

    for (period, student_key), data in day_store.items():
        if not isinstance(data, dict):
            data = {"letter": sanitize_letter(str(data)), "absent": False}

        letter = sanitize_letter(data.get("letter", ""))
        absent = bool(data.get("absent", False))

        if not letter and not absent:
            continue

        rows.append([
            date_key,
            int(period),
            str(student_key),
            letter,
            absent,
            updated_at,
            batch_id,
        ])

    return rows


def deserialize_attendance_rows(records: list[dict]) -> DayStore:
    day_store: DayStore = {}

    for row in records:
        try:
            period = int(row.get(COL_ATT_PERIOD, 0))
        except Exception:
            continue

        student_key = str(row.get(COL_ATT_STUDENT_KEY, "")).strip()
        if not student_key or period <= 0:
            continue

        absent_raw = row.get(COL_ATT_ABSENT, False)
        absent = str(absent_raw).strip().upper() in {"TRUE", "1", "Y", "YES"}

        day_store[(period, student_key)] = {
            "letter": sanitize_letter(row.get(COL_ATT_LETTER, "")),
            "absent": absent,
        }

    return day_store


def save_attendance_for_date(date_key: str, day_store: DayStore) -> None:
    sh = _get_spreadsheet()
    ws = _get_or_create_worksheet(
        sh,
        WORKSHEET_ATTENDANCE_DATA,
        ATTENDANCE_DATA_COLUMNS,
    )
    batch_id = _new_batch_id(ATTENDANCE_BATCH_PREFIX)
    new_rows = serialize_day_store(date_key, day_store, batch_id)
    # 공백만 있는 저장은 기록하지 않음
    if not new_rows:
        return
    ws.append_rows(new_rows, value_input_option="USER_ENTERED")

def load_attendance_for_date(date_key: str) -> DayStore:
    sh = _get_spreadsheet()
    ws = _get_or_create_worksheet(
        sh,
        WORKSHEET_ATTENDANCE_DATA,
        ATTENDANCE_DATA_COLUMNS,
    )
    records = ws.get_all_records()
    rows = [r for r in records if str(r.get(COL_ATT_DATE, "")).strip() == date_key]
    if not rows:
        return {}
    df = pd.DataFrame(rows)
    if df.empty:
        return {}
    # batch_id가 없으면 예전 방식 fallback
    if COL_ATT_BATCH_ID not in df.columns:
        return deserialize_attendance_rows(rows)
    # 시트에 append된 순서를 보존
    df["_row_order"] = range(len(df))
    # 마지막 행의 batch_id를 최신 저장 묶음으로 간주
    latest_batch_id = str(df.iloc[-1][COL_ATT_BATCH_ID]).strip()
    latest_rows = (
        df[df[COL_ATT_BATCH_ID] == latest_batch_id]
        .sort_values("_row_order")
        .to_dict("records")
    )
    return deserialize_attendance_rows(latest_rows)

def save_students_monthly_snapshot(snapshot_month: str, df: pd.DataFrame) -> None:
    sh = _get_spreadsheet()
    ws = _get_or_create_worksheet(
        sh,
        WORKSHEET_STUDENTS_MONTHLY_DATA,
        STUDENTS_MONTHLY_DATA_COLUMNS,
    )

    saved_at = now_kst().strftime("%Y-%m-%d %H:%M:%S")
    batch_id = _new_batch_id(MONTHLY_BATCH_PREFIX)

    rows: list[list[Any]] = []
    target_cols = [COL_ID, COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS]

    for _, r in df[target_cols].iterrows():
        rows.append([
            snapshot_month,
            saved_at,
            batch_id,
            r.get(COL_ID, ""),
            r.get(COL_NAME, ""),
            r.get(COL_SCHOOL, ""),
            r.get(COL_GRADE, ""),
            r.get(COL_DAYS, ""),
            r.get(COL_PERIOD, ""),
            r.get(COL_STATUS, ""),
        ])

    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")


def load_students_monthly_snapshot(snapshot_month: str) -> pd.DataFrame:
    sh = _get_spreadsheet()
    ws = _get_or_create_worksheet(
        sh,
        WORKSHEET_STUDENTS_MONTHLY_DATA,
        STUDENTS_MONTHLY_DATA_COLUMNS,
    )

    records = ws.get_all_records()
    rows = [r for r in records if str(r.get(COL_MONTHLY_MONTH, "")).strip() == snapshot_month]

    if not rows:
        return pd.DataFrame(columns=STUDENTS_MONTHLY_DATA_COLUMNS)

    df = pd.DataFrame(rows)

    if COL_MONTHLY_BATCH_ID not in df.columns:
        return df

    df[COL_MONTHLY_SAVED_AT] = df[COL_MONTHLY_SAVED_AT].astype(str)

    batch_time = (
        df.groupby(COL_MONTHLY_BATCH_ID)[COL_MONTHLY_SAVED_AT]
        .max()
        .reset_index()
        .sort_values(COL_MONTHLY_SAVED_AT)
    )

    latest_batch_id = batch_time.iloc[-1][COL_MONTHLY_BATCH_ID]
    latest_df = df[df[COL_MONTHLY_BATCH_ID] == latest_batch_id].copy()

    return latest_df.reset_index(drop=True)


def save_teacher_notes_for_date(date_key: str, teacher_notes: dict[int, str]) -> None:
    sh = _get_spreadsheet()
    ws = _get_or_create_worksheet(
        sh,
        WORKSHEET_ATTENDANCE_TEACHER_NOTES,
        ATTENDANCE_TEACHER_NOTE_COLUMNS,
    )

    updated_at = now_kst().strftime("%Y-%m-%d %H:%M:%S")

    rows = []
    for period in [1, 2, 3]:
        note = str(teacher_notes.get(period, "")).strip()
        rows.append([
            date_key,
            period,
            note,
            updated_at,
        ])

    if rows:
        ws.append_rows(rows, value_input_option="USER_ENTERED")

def load_teacher_notes_for_date(date_key: str) -> dict[int, str]:
    sh = _get_spreadsheet()
    ws = _get_or_create_worksheet(
        sh,
        WORKSHEET_ATTENDANCE_TEACHER_NOTES,
        ATTENDANCE_TEACHER_NOTE_COLUMNS,
    )

    records = ws.get_all_records()
    rows = [r for r in records if str(r.get(COL_TNOTE_DATE, "")).strip() == date_key]

    result = {1: "", 2: "", 3: ""}
    if not rows:
        return result

    df = pd.DataFrame(rows)

    if df.empty:
        return result

    if COL_TNOTE_UPDATED_AT in df.columns:
        df[COL_TNOTE_UPDATED_AT] = df[COL_TNOTE_UPDATED_AT].astype(str)

    latest_by_period = (
        df.sort_values(COL_TNOTE_UPDATED_AT)
          .drop_duplicates(subset=[COL_TNOTE_PERIOD], keep="last")
    )

    for _, row in latest_by_period.iterrows():
        try:
            period = int(row.get(COL_TNOTE_PERIOD, 0))
        except Exception:
            continue

        if period in [1, 2, 3]:
            result[period] = str(row.get(COL_TNOTE_NOTE, "")).strip()

    return result

def save_weekly_period_notes(period_notes: dict[int, str], source: str = "current") -> None:
    sh = _get_spreadsheet()
    ws = _get_or_create_worksheet(
        sh,
        WORKSHEET_WEEKLY_PERIOD_NOTES,
        WEEKLY_PERIOD_NOTE_COLUMNS,
    )
    updated_at = now_kst().strftime("%Y-%m-%d %H:%M:%S")
    source = str(source).strip().lower() or "current"
    rows = []
    for period, note in period_notes.items():
        try:
            p = int(period)
        except Exception:
            continue
        if p <= 0:
            continue
        rows.append([
            source,
            p,
            str(note).strip(),
            updated_at,
        ])
    all_values = ws.get_all_values()
    if not all_values:
        ws.append_row(WEEKLY_PERIOD_NOTE_COLUMNS)
        all_values = [WEEKLY_PERIOD_NOTE_COLUMNS]
    keep_rows = [all_values[0]]
    existing_keys = {(source, str(int(p))) for p in period_notes.keys()}
    for row in all_values[1:]:
        row_source = str(row[0]).strip().lower() if len(row) > 0 else ""
        row_period = str(row[1]).strip() if len(row) > 1 else ""
        if (row_source, row_period) not in existing_keys:
            keep_rows.append(row)
    ws.clear()
    ws.update("A1", keep_rows)
    if rows:
        start_row = len(keep_rows) + 1
        end_row = start_row + len(rows) - 1
        ws.update(f"A{start_row}:D{end_row}", rows)


def load_weekly_period_notes(source: str = "current") -> dict[int, str]:
    sh = _get_spreadsheet()
    ws = _get_or_create_worksheet(
        sh,
        WORKSHEET_WEEKLY_PERIOD_NOTES,
        WEEKLY_PERIOD_NOTE_COLUMNS,
    )
    records = ws.get_all_records()
    source = str(source).strip().lower() or "current"
    result: dict[int, str] = {}
    for row in records:
        row_source = str(row.get(COL_WPN_SOURCE, "")).strip().lower()
        if row_source != source:
            continue
        try:
            period = int(row.get(COL_WPN_PERIOD, 0))
        except Exception:
            continue
        if period <= 0:
            continue
        result[period] = str(row.get(COL_WPN_NOTE, "")).strip()
    return result