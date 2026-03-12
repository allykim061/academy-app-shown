# academy/ui.py
import streamlit as st
import pandas as pd

from .config import (
    COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS,
    GRADE_ORDER, WEEKDAY_ORDER
)
from .data import load_data
from .styles import get_print_css_cached
from .tables import (
    generate_total_list_html,
    generate_table1, generate_table2, generate_table3, generate_table4
)
from .filters import filter_students_for_day_period
from .utils import get_student_key, sanitize_letter, now_kst, today_kst, split_days, match_attendance
from .backup import (
    save_attendance_for_date, load_attendance_for_date,
    save_teacher_notes_for_date, load_teacher_notes_for_date,
    load_weekly_slot_memos, save_weekly_slot_memos,
    load_weekly_period_notes, save_weekly_period_notes,
)

def run_app():
    df = load_data()

    print_banner = (
        '<div class="no-print" style="background-color:#f1f3f5;padding:15px;border-radius:8px;'
        'border-left:5px solid #868396;margin-bottom:20px;">🖨️ 인쇄: 우측 상단 ⋮ ➜ Print 선택</div>'
    )

    # ✅ 배정 저장소(session_state)
    if "assignments" not in st.session_state:
        st.session_state["assignments"] = {}  # {date_iso: {(period, student_key): {"letter": "", "absent": False, "memo": ""}}}

    # 사이드바
    with st.sidebar:
        print_orientation = st.radio("용지 방향", ["세로", "가로"])
        st.markdown(get_print_css_cached(print_orientation), unsafe_allow_html=True)

        if st.button("새로고침"):
            st.cache_data.clear()
            st.rerun()

    tab_list = st.tabs(["전체 목록", "학년별 명단", "수업시간 명단", "출석부", "학교별 명단"])

   # 탭 0
    with tab_list[0]:
        st.markdown(print_banner, unsafe_allow_html=True)
        if not df.empty:
            display_df = df[[COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS]]
            total_n = len(display_df)

            q = (st.session_state.get("tab0_search", "") or "").strip()

            if q:
                mask = display_df.apply(
                    lambda col: col.astype(str).str.contains(q, case=False, na=False)
                ).any(axis=1)
                filtered_df = display_df[mask]
            else:
                filtered_df = display_df

            # ✅ 화면용 UI는 no-print로 감싸서 인쇄에서 완전 제거
            st.markdown("<div class='no-print'>", unsafe_allow_html=True)

            col_title, col_tools = st.columns([3, 2], vertical_alignment="bottom")
            with col_title:
                st.markdown(
                    f"""
                    <h2 class="no-print" style="font-size:16pt; margin:0;">
                        등록 학생 목록
                        <span style="font-size:11pt; color:#666;">[총 {total_n}명]</span>
                    </h2>
                    """,
                    unsafe_allow_html=True
                )

            with col_tools:
                col_reset, col_input = st.columns([1.0, 4.5], vertical_alignment="bottom")
                with col_reset:
                    if q:
                        if st.button("Reset", use_container_width=True):
                            st.session_state["tab0_search"] = ""
                            st.rerun()
                    else:
                        st.empty()

                with col_input:
                    st.text_input("", placeholder="🔍 Search", label_visibility="collapsed", key="tab0_search")

            col_left_blank, col_right_msg = st.columns([3, 2])
            with col_right_msg:
                col_reset_spacer, col_msg = st.columns([1.0, 4.5])
                with col_reset_spacer:
                    st.empty()
                with col_msg:
                    q_now = (st.session_state.get("tab0_search", "") or "").strip()
                    msg = f"'{q_now}' 검색 결과: {len(filtered_df)}명" if q_now else "&nbsp;"
                    
                    # 💡 div 안에 class='no-print' 를 추가
                    st.markdown(
                        f"<div class='no-print' style='font-size:12px;color:#666;text-align:left;margin-top:-6px;min-height:18px;'>{msg}</div>",
                        unsafe_allow_html=True
                    )

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

            height = len(filtered_df) * 35 + 40
            st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=height)

            st.markdown("</div>", unsafe_allow_html=True)  # ✅ no-print 닫기

            # ✅ 인쇄 전용(제목+표)만 남김
            # 💡 인쇄용 검색 결과 텍스트 생성 (없으면 빈칸)

            q_now = (st.session_state.get("tab0_search", "") or "").strip()
            print_msg = f"'{q_now}' 검색 결과: {len(filtered_df)}명" if q_now else ""

            st.markdown(
                f"""
                <div class="tab0-print-root">
                    <div class="tab0-print-header">
                        <h2 class="tab0-print-title">
                            등록 학생 목록 <span class="tab0-print-count">[총 {total_n}명]</span>
                        </h2>
                        <div class="tab0-print-search-msg">{print_msg}</div>
                    </div>
                    {generate_total_list_html(filtered_df)}
                </div>
                """,
                unsafe_allow_html=True
            )

    # 탭 1
    with tab_list[1]:
        st.markdown(print_banner, unsafe_allow_html=True)
        if not df.empty:
            col1, col2 = st.columns([3, 1])
            with col1:
                m1 = st.text_input("제목(연/월)", value=now_kst().strftime("%Y.%m"), key="m1")
            with col2:
                show_school_t1 = st.checkbox("학교명 표시", value=True, key="chk_school_m1")
                show_count_t1 = st.checkbox("학교별 인원수 표시", value=True, key="chk_count_m1")

            st.markdown(
                f"<div class='a4-print-box'><div class='report-view'>{generate_table1(df, show_school_t1, show_count_t1, m1)}</div></div>",
                unsafe_allow_html=True,
            )

    # 탭 2
    with tab_list[2]:
        st.markdown(print_banner, unsafe_allow_html=True)
        if not df.empty:
            st.markdown("<div class='no-print'>", unsafe_allow_html=True)

            top_col1, top_col2 = st.columns(2)

            with top_col1:
                m2 = st.text_input("하단 표기", value=now_kst().strftime("%Y-%m"), key="m2")

            with top_col2:
                selected_period = st.selectbox(
                    "편집할 교시",
                    [1, 2, 3],
                    format_func=lambda x: f"{x}교시",
                    key="weekly_selected_period"
                )
            # 2번표 저장값 로드
            weekly_slot_memo_key = "weekly_slot_memos"
            if weekly_slot_memo_key not in st.session_state:
                try:
                    st.session_state[weekly_slot_memo_key] = load_weekly_slot_memos()
                except Exception:
                    st.session_state[weekly_slot_memo_key] = {}

            weekly_period_note_key = "weekly_period_notes"
            if weekly_period_note_key not in st.session_state:
                try:
                    st.session_state[weekly_period_note_key] = load_weekly_period_notes()
                except Exception:
                    st.session_state[weekly_period_note_key] = {1: "", 2: "", 3: ""}

            # 재원생만 사용
            df_active = df[df[COL_STATUS] == "재원"].copy()

            grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}
            df_active["_grade_order"] = df_active[COL_GRADE].map(grade_sort_map).fillna(999)
            df_active = df_active.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])

            target_days = ["월", "화", "수", "목"]

            st.markdown(
                """
                <div class="no-print">
                    <h3 style="margin:0 0 6px 0;">메모 입력</h3>
                    <div style="font-size:12px; color:#666; margin-bottom:8px;">
                        메모 최대 6자, 학년 칸에 입력하지 마세요.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 선택 교시의 요일별 학생 목록
            slot_students = {}
            for day in target_days:
                condition = df_active.apply(
                    lambda row: match_attendance(row[COL_DAYS], row[COL_PERIOD], day, selected_period),
                    axis=1
                )
                slot_students[day] = df_active[condition].copy()

            def render_weekly_day_cell(container, df_slot: pd.DataFrame, day: str, period: int, edited_slot_memos: dict):
                with container:
                    if df_slot.empty:
                        st.caption("—")
                        return

                    editor_rows = []
                    last_grade = None

                    for _, row in df_slot.iterrows():
                        skey = get_student_key(row)
                        school = str(row[COL_SCHOOL]).strip()
                        grade = str(row[COL_GRADE]).strip()

                        # 학년이 바뀌면 제목 행 추가
                        if last_grade is None or grade != last_grade:
                            editor_rows.append({
                                "_slot_key": f"__grade__|{day}|{period}|{grade}",
                                "이름": f"【{grade}】",
                                "메모": "⸺⸺⸺⸺",
                            })

                        slot_key = (day, period, skey)
                        slot_key_str = f"{day}|{period}|{skey}"

                        editor_rows.append({
                            "_slot_key": slot_key_str,
                            "이름": f"{row[COL_NAME]}({school})",
                            "메모": edited_slot_memos.get(
                                slot_key,
                                st.session_state[weekly_slot_memo_key].get(slot_key, "")
                            ),
                        })

                        last_grade = grade

                    df_editor = pd.DataFrame(editor_rows)
                    dynamic_height = (len(df_editor) * 35) + 40

                    edited_df = st.data_editor(
                        df_editor,
                        height=dynamic_height,
                        column_order=["이름", "메모"],
                        column_config={
                            "_slot_key": None,
                            "이름": st.column_config.TextColumn("이름", disabled=True, width="small"),
                            "메모": st.column_config.TextColumn("메모", max_chars=6, width="small"),
                        },
                        hide_index=True,
                        key=f"weekly_editor_{day}_{period}",
                        use_container_width=True,
                    )

                    for _, erow in edited_df.iterrows():
                        slot_key_str = str(erow["_slot_key"])

                        if slot_key_str.startswith("__grade__|"):
                            continue

                        day_str, period_str, student_key = slot_key_str.split("|", 2)
                        slot_key = (day_str, int(period_str), student_key)
                        edited_slot_memos[slot_key] = str(erow.get("메모", "")).strip()

            with st.form(key=f"weekly_memo_form_{selected_period}", clear_on_submit=False):
                header_cols = st.columns([0.65, 1.85, 1.85, 1.85, 1.85])
                header_labels = ["수업시간", "월", "화", "수", "목"]
                for col, label in zip(header_cols, header_labels):
                    with col:
                        st.markdown(
                            f"""
                            <div class="no-print" style="
                                border:1px solid #dee2e6;
                                background:#f8f9fa;
                                padding:8px 6px;
                                text-align:center;
                                font-weight:600;
                                font-size:13px;
                                border-radius:6px;
                                margin-bottom:6px;
                            ">
                                {label}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                edited_slot_memos = {}
                row_cols = st.columns([0.65, 1.85, 1.85, 1.85, 1.85], vertical_alignment="top")

                with row_cols[0]:
                    st.markdown(
                        f"""
                        <div class="no-print" style="
                            border:1px solid #dee2e6;
                            background:#fafafa;
                            padding:10px 6px;
                            text-align:center;
                            font-weight:600;
                            font-size:13px;
                            border-radius:6px;
                        ">
                            {selected_period}교시
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                render_weekly_day_cell(row_cols[1], slot_students["월"], "월", selected_period, edited_slot_memos)
                render_weekly_day_cell(row_cols[2], slot_students["화"], "화", selected_period, edited_slot_memos)
                render_weekly_day_cell(row_cols[3], slot_students["수"], "수", selected_period, edited_slot_memos)
                render_weekly_day_cell(row_cols[4], slot_students["목"], "목", selected_period, edited_slot_memos)

                st.markdown(
                    """
                    <div class="no-print" style="margin-top:14px; margin-bottom:6px; display:flex; align-items:baseline; gap:8px;">
                        <div style="font-weight:600; font-size:13px;">비고</div>
                        <div style="font-size:11px; color:#363636;">인쇄: 한 줄에 세로 11자, 가로 17자까지 입력 가능</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                note_val = st.text_area(
                    "",
                    value=st.session_state[weekly_period_note_key].get(selected_period, ""),
                    key=f"weekly_period_note_{selected_period}",
                    height=180,
                    label_visibility="collapsed",
                )

                btn_apply, btn_save, btn_blank = st.columns([1, 1, 6])

                with btn_apply:
                    apply_weekly_memo_clicked = st.form_submit_button("적용", use_container_width=True)

                with btn_save:
                    save_weekly_memo_clicked = st.form_submit_button("저장", use_container_width=True, type="primary")

            if apply_weekly_memo_clicked or save_weekly_memo_clicked:
                merged_slot_memos = dict(st.session_state[weekly_slot_memo_key])
                merged_slot_memos.update(edited_slot_memos)

                merged_period_notes = dict(st.session_state[weekly_period_note_key])
                merged_period_notes[selected_period] = str(note_val).strip()

                st.session_state[weekly_slot_memo_key] = merged_slot_memos
                st.session_state[weekly_period_note_key] = merged_period_notes

                st.success("인쇄에 반영되었습니다.")

            if save_weekly_memo_clicked:
                try:
                    save_weekly_slot_memos(st.session_state[weekly_slot_memo_key])
                    save_weekly_period_notes(st.session_state[weekly_period_note_key])
                    st.success("저장 완료, 인쇄에 반영됩니다")
                except Exception as e:
                    st.error(f"저장 실패: {e}")

            st.markdown(
                """
                <div class="no-print">
                    <h3 style="margin:0 0 8px 0;">🖨️ 미리보기</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(
                f"<div class='a4-print-box'><div class='report-view'>{generate_table2(df, m2, st.session_state[weekly_slot_memo_key], st.session_state[weekly_period_note_key])}</div></div>",
                unsafe_allow_html=True
            )

    # 탭 3
    with tab_list[3]:
        st.markdown(print_banner, unsafe_allow_html=True)

        if not df.empty:
            st.markdown("<div id='t3-top'></div>", unsafe_allow_html=True)

            # 네비 버튼 스타일 + 인쇄 시 입력 UI 숨김
            st.markdown("""
            <style>
            .nav-btn {
                display: inline-block;
                padding: 6px 14px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                color: #495057 !important;
                text-decoration: none !important;
                font-size: 13px;
                font-weight: 500;
                transition: all 0.2s;
                white-space: nowrap;
            }
            .nav-btn:hover {
                background-color: #e9ecef;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .section-nav-row {
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                margin-top: 20px;
                margin-bottom: 8px;
            }
            .section-nav-row h3 {
                margin: 0;
                padding: 0;
            }

            @media print {
                [data-testid="stDateInput"],
                [data-testid="stForm"],
                [data-testid="stCaptionContainer"],
                [data-testid="stAlert"] {
                    display: none !important;
                }
            }
            </style>
            """, unsafe_allow_html=True)

            # 날짜 선택
            d3 = st.date_input("날짜 선택", value=today_kst())
            weekday = WEEKDAY_ORDER[d3.weekday()]
            date_key = d3.isoformat()

            # 저장 데이터 불러오기
            if date_key not in st.session_state["assignments"]:
                try:
                    restored = load_attendance_for_date(date_key)
                    st.session_state["assignments"][date_key] = restored
                except Exception:
                    st.session_state["assignments"][date_key] = {}

            day_store = st.session_state["assignments"][date_key]

            # 날짜별 editor/widget 버전값
            editor_version_key = f"attendance_editor_version_{date_key}"
            if editor_version_key not in st.session_state:
                st.session_state[editor_version_key] = 0
            editor_version = st.session_state[editor_version_key]

            # 집계 결과 저장소
            summary_key = f"attendance_summary_{date_key}"
            if summary_key not in st.session_state:
                st.session_state[summary_key] = {}

            # 교시별 담당/메모 저장소
            teacher_note_key = f"teacher_notes_{date_key}"
            if teacher_note_key not in st.session_state:
                try:
                    st.session_state[teacher_note_key] = load_teacher_notes_for_date(date_key)
                except Exception:
                    st.session_state[teacher_note_key] = {1: "", 2: "", 3: ""}

            # 해당 요일 + 재원만
            day_mask = df[COL_DAYS].astype(str).apply(lambda x: weekday in split_days(x))
            df_day = df[day_mask].copy()
            df_day = df_day[df_day[COL_STATUS] == "재원"]

            grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}

            # 교시별 학생 목록
            per_period_students = {}
            for p in [1, 2, 3]:
                df_p = filter_students_for_day_period(df_day, weekday, p).copy()
                df_p["_grade_order"] = df_p[COL_GRADE].map(grade_sort_map).fillna(999)
                df_p = df_p.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])
                per_period_students[p] = df_p

            # 입력 영역 제목 + 우측 네비
            st.markdown(
                """
                <div class="no-print section-nav-row">
                    <h3>📝 배정 · 결석 입력</h3>
                    <a href="#t3-preview" class="nav-btn">🖨️ 미리보기</a>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption("💡 배정: 알파벳 1글자 입력 · Enter / 방향키 이동")

            summary_clicked = False
            apply_clicked = False
            save_clicked = False
            reset_clicked = False

            # 입력표 시작 직전 anchor
            st.markdown("<div id='t3-editor'></div>", unsafe_allow_html=True)

            def build_period_summary(df_edited: pd.DataFrame | None) -> dict:
                if df_edited is None or df_edited.empty:
                    return {
                        "total": 0,
                        "absent": 0,
                        "letters": {}
                    }

                total = len(df_edited)
                absent = int(df_edited["결석"].fillna(False).astype(bool).sum())

                letters = {}
                for raw in df_edited["배정"].fillna(""):
                    letter = sanitize_letter(raw)
                    if letter:
                        letters[letter] = letters.get(letter, 0) + 1

                return {
                    "total": total,
                    "absent": absent,
                    "letters": dict(sorted(letters.items()))
                }

            with st.form(key=f"assign_form_{date_key}_{editor_version}", clear_on_submit=False):
                has_p1 = not per_period_students.get(1, pd.DataFrame()).empty
                has_p2 = not per_period_students.get(2, pd.DataFrame()).empty
                has_p3 = not per_period_students.get(3, pd.DataFrame()).empty

                if has_p1 and has_p2 and not has_p3:
                    ec1, ec2, ec3 = st.columns([1, 1, 0.35])
                elif has_p1 and not has_p2 and has_p3:
                    ec1, ec2, ec3 = st.columns([1, 0.35, 1])
                elif not has_p1 and has_p2 and has_p3:
                    ec1, ec2, ec3 = st.columns([0.35, 1, 1])
                else:
                    ec1, ec2, ec3 = st.columns(3)
                edited_dfs = {}

                def render_data_editor(col, p):
                    with col:
                        st.markdown(f"**{p}교시**")
                        df_p = per_period_students.get(p, pd.DataFrame())
                        if df_p.empty:
                            st.caption("해당 교시 학생 없음")
                            return None

                        editor_data = []
                        for _, row in df_p.iterrows():
                            skey = get_student_key(row)

                            current = day_store.get((p, skey), {})
                            if isinstance(current, str):
                                c_let = sanitize_letter(current)
                                c_abs = False
                                c_memo = ""
                            else:
                                c_let = sanitize_letter(current.get("letter", ""))
                                c_abs = bool(current.get("absent", False))
                                c_memo = str(current.get("memo", "")).strip()

                            school = str(row[COL_SCHOOL]).strip()
                            grade = str(row[COL_GRADE]).strip()
                            school_grade = school + (grade[1:] if school and grade and school[-1] == grade[0] else grade)

                            editor_data.append({
                                "_skey": skey,
                                "이름": f"{row[COL_NAME]} ({school_grade})",
                                "메모": c_memo,
                                "배정": c_let,
                                "결석": c_abs,
                            })

                        df_editor = pd.DataFrame(editor_data)
                        dynamic_height = (len(df_editor) * 35) + 40

                        edited_df = st.data_editor(
                            df_editor,
                            height=dynamic_height,
                            column_order=["이름", "메모", "배정", "결석"],
                            column_config={
                                "_skey": None,
                                "이름": st.column_config.TextColumn("이름", disabled=True),
                                "메모": st.column_config.TextColumn("메모", max_chars=6),
                                "배정": st.column_config.TextColumn("배정", max_chars=1),
                                "결석": st.column_config.CheckboxColumn("결석"),
                            },
                            hide_index=True,
                            key=f"editor_{date_key}_{p}_{editor_version}",
                            use_container_width=True,
                        )
                        return edited_df

                edited_dfs[1] = render_data_editor(ec1, 1)
                edited_dfs[2] = render_data_editor(ec2, 2)
                edited_dfs[3] = render_data_editor(ec3, 3)

                # 교시별 담당/메모 입력 (form 안)
                st.markdown(
                    """
                    <div class="no-print" style="margin-top:12px; margin-bottom:8px;">
                        <h4 style="margin:0 0 6px 0; font-size:14px;">메모</h4>
                        <div style="font-size:12px; color:#666;">
                            한 줄에 8~10자 정도 입력
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                tn1, tn2, tn3 = st.columns(3)

                with tn1:
                    note_1 = st.text_area(
                        "1교시",
                        value=st.session_state[teacher_note_key].get(1, ""),
                        height=110,
                        key=f"teacher_note_1_{date_key}_{editor_version}",
                    )

                with tn2:
                    note_2 = st.text_area(
                        "2교시",
                        value=st.session_state[teacher_note_key].get(2, ""),
                        height=110,
                        key=f"teacher_note_2_{date_key}_{editor_version}",
                    )

                with tn3:
                    note_3 = st.text_area(
                        "3교시",
                        value=st.session_state[teacher_note_key].get(3, ""),
                        height=110,
                        key=f"teacher_note_3_{date_key}_{editor_version}",
                    )

                btn_summary, btn_apply, btn_save, btn_reset, btn_blank = st.columns([1.2, 1, 1, 1, 6.8])

                with btn_summary:
                    summary_clicked = st.form_submit_button("합계", use_container_width=True)

                with btn_apply:
                    apply_clicked = st.form_submit_button("적용", use_container_width=True)

                with btn_save:
                    save_clicked = st.form_submit_button("저장", use_container_width=True, type="primary")

                with btn_reset:
                    reset_clicked = st.form_submit_button("초기화", use_container_width=True)

            if reset_clicked:
                st.session_state["assignments"][date_key] = {}
                st.session_state[summary_key] = {}
                st.session_state[teacher_note_key] = {1: "", 2: "", 3: ""}
                st.session_state.pop(f"preview_html_{date_key}", None)
                st.session_state[editor_version_key] += 1
                st.rerun()

            if summary_clicked:
                summary_result = {}
                for p in [1, 2, 3]:
                    df_edited = edited_dfs.get(p)
                    summary_result[p] = build_period_summary(df_edited)
                st.session_state[summary_key] = summary_result

            if apply_clicked or save_clicked:
                for p in [1, 2, 3]:
                    df_edited = edited_dfs.get(p)
                    if df_edited is not None and not df_edited.empty:
                        for _, row in df_edited.iterrows():
                            skey = row["_skey"]
                            v_let = row["배정"]
                            v_abs = row["결석"]
                            v_memo = str(row.get("메모", "")).strip()

                            day_store[(p, skey)] = {
                                "letter": sanitize_letter(v_let),
                                "absent": bool(v_abs),
                                "memo": v_memo,
                            }

                st.success("저장 완료, 인쇄에 반영됩니다.")

                # 집계 갱신
                summary_result = {}
                for p in [1, 2, 3]:
                    df_edited = edited_dfs.get(p)
                    summary_result[p] = build_period_summary(df_edited)
                st.session_state[summary_key] = summary_result

            # 집계 표시
            summary_data = st.session_state.get(summary_key, {})
            if summary_data:
                st.markdown(
                    """
                    <div class="no-print" style="margin-top:18px; margin-bottom:10px;">
                        <h4 style="margin:0 0 8px 0; font-size:14px;">교시별 합계</h4>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                sc1, sc2, sc3 = st.columns(3)

                def render_summary_card(col, p):
                    with col:
                        data = summary_data.get(p, {"total": 0, "absent": 0, "letters": {}})
                        lines = [f"인원 | {data['total']}명"]

                        for letter, count in data["letters"].items():
                            lines.append(f"{letter} | {count}명")

                        lines.append(f"결석 | {data['absent']}명")

                        body = "<br>".join(lines)

                        st.markdown(
                            f"""
                            <div class="no-print" style="
                                border:1px solid #dee2e6;
                                border-radius:8px;
                                background:#f8f9fa;
                                padding:10px 12px;
                                margin-bottom:10px;
                                font-size:13px;
                                line-height:1.7;
                            ">
                                <div style="font-weight:600; margin-bottom:6px;">{p}교시 합계</div>
                                <div>{body}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                render_summary_card(sc1, 1)
                render_summary_card(sc2, 2)
                render_summary_card(sc3, 3)
           
            if apply_clicked or save_clicked:
                st.session_state[teacher_note_key] = {
                    1: str(note_1).strip(),
                    2: str(note_2).strip(),
                    3: str(note_3).strip(),
                }

                st.session_state[f"preview_html_{date_key}"] = generate_table3(
                    df,
                    d3,
                    False,
                    day_store,
                    st.session_state.get(teacher_note_key, {1: "", 2: "", 3: ""}),
                )

            if save_clicked:
                try:
                    save_attendance_for_date(date_key, day_store)
                    save_teacher_notes_for_date(date_key, st.session_state[teacher_note_key])
                    st.success("저장 완료")
                except Exception as e:
                    st.error(f"저장 실패: {e}")

            # 출력 영역 제목 + 우측 네비
            st.markdown(
                """
                <div class="no-print section-nav-row" style="margin-top:40px; border-top:2px dashed #dee2e6; padding-top:20px;">
                    <h3>🖨️ 미리보기</h3>
                    <div style="display:flex; gap:10px;">
                        <a href="#t3-editor" class="nav-btn">✏️ 입력창으로</a>
                        <a href="#t3-bottom" class="nav-btn">⬇️ 하단 이동</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 출력표 시작 직전 anchor
            st.markdown("<div id='t3-preview'></div>", unsafe_allow_html=True)

            preview_key = f"preview_html_{date_key}"
            if preview_key not in st.session_state:
                st.session_state[preview_key] = generate_table3(
                    df,
                    d3,
                    False,
                    day_store,
                    st.session_state.get(teacher_note_key, {1: "", 2: "", 3: ""}),
                )

            st.markdown(
                f"<div class='a4-print-box'><div class='report-view'>{st.session_state[preview_key]}</div></div>",
                unsafe_allow_html=True
            )

            # 하단 anchor
            st.markdown("<div id='t3-bottom'></div>", unsafe_allow_html=True)

            # 하단 네비
            st.markdown(
                """
                <div class="no-print" style="display:flex; justify-content:flex-end; gap:10px; margin-top:15px; margin-bottom:20px;">
                    <a href="#t3-editor" class="nav-btn">✏️ 입력창으로</a>
                    <a href="#t3-preview" class="nav-btn">🖨️ 미리보기</a>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    # 탭 4
    with tab_list[4]:
        st.markdown(print_banner, unsafe_allow_html=True)
        if not df.empty:
            m4 = st.text_input("제목(연/월)", value=now_kst().strftime("%Y.%m"), key="m4")
            st.markdown(f"<div class='a4-print-box'><div class='report-view'>{generate_table4(df, True, m4)}</div></div>", unsafe_allow_html=True)