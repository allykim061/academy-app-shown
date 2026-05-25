# academy/ui.py
import streamlit as st
import pandas as pd

from .config import (
    COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS,
    COL_STUDENT_MEMO,
    GRADE_ORDER, WEEKDAY_ORDER,
    WORKSHEET_STUDENTS, WORKSHEET_STUDENTS_NEXT,
)
from .data import load_data
from .styles import get_print_css_cached
from .tables import (
    generate_total_list_html,
    generate_table1, generate_table2, generate_table3, generate_table4
)
from .filters import filter_students_for_day_period
from .utils import get_student_key, sanitize_letter, now_kst, today_kst, split_days
from .backup import (
    save_attendance_for_date, load_attendance_for_date,
    save_teacher_notes_for_date, load_teacher_notes_for_date,
    save_weekly_period_notes, load_weekly_period_notes,
)

def get_next_month_yyyy_mm():
    now = now_kst()
    year = now.year
    month = now.month + 1
    if month == 13:
        year += 1
        month = 1
    return f"{year:04d}-{month:02d}"

def run_app():
    df = load_data()

    print_banner = (
        '<div class="no-print" style="background-color:#f1f3f5;padding:15px;border-radius:8px;'
        'border-left:5px solid #868396;margin-bottom:20px;">🖨️ 인쇄: 우측 상단 ⋮ ➜ Print 선택</div>'
    )

    if "assignments" not in st.session_state:
        st.session_state["assignments"] = {}

    with st.sidebar:
        print_orientation = st.radio("용지 방향", ["세로", "가로"])
        st.markdown(get_print_css_cached(print_orientation), unsafe_allow_html=True)

    blank = "\u2003" * 2
    page_labels = {
        "tab0": f"{blank}전체 목록{blank}",
        "tab1": f"{blank}학년별 명단{blank}",
        "tab2": f"{blank}전체 출석부{blank}",
        "tab3": f"{blank}일일 출석부{blank}",
        "tab4": f"{blank}학교별 명단{blank}",
    }
    selected_label = st.segmented_control(
        "메뉴",
        list(page_labels.values()),
        selection_mode="single",
        default=page_labels["tab0"],
        key="main_page",
        label_visibility="collapsed",
    ) or page_labels["tab0"]
    label_to_page = {label: key for key, label in page_labels.items()}
    page = label_to_page.get(selected_label, "tab0")

    with st.sidebar:
        if st.button("새로고침"):
            st.cache_data.clear()

            keys_to_delete = []

            if page == "tab0":
                keys_to_delete.extend([
                    "tab0_search",
                ])

            elif page == "tab1":
                keys_to_delete.extend([
                    "m1",
                    "chk_school_m1",
                    "chk_count_m1",
                ])

            elif page == "tab2":
                keys_to_delete.extend([
                    "table2_source_label",
                    "m2_current",
                    "m2_next",
                ])

                for k in list(st.session_state.keys()):
                    if (
                        k.startswith("weekly_note_msg_")
                        or k.startswith("weekly_note_error_")
                        or k.startswith("weekly_period_notes_")
                        or k.startswith("chk_show_period_notes_t2_")
                        or k.startswith("weekly_selected_period_note_")
                        or k.startswith("weekly_period_note_input_")
                    ):
                        keys_to_delete.append(k)

            elif page == "tab3":
                for k in list(st.session_state.keys()):
                    if (
                        k.startswith("attendance_editor_version_")
                        or k.startswith("attendance_summary_")
                        or k.startswith("teacher_notes_")
                        or k.startswith("attendance_save_in_progress_")
                        or k.startswith("attendance_preview_html_")
                        or k.startswith("attendance_preview_dirty_")
                        or k.startswith("attendance_summary_msg_")
                        or k.startswith("attendance_status_msg_")
                    ):
                        keys_to_delete.append(k)
                st.session_state["assignments"] = {}

            elif page == "tab4":
                keys_to_delete.extend([
                    "m4",
                ])

            for k in set(keys_to_delete):
                if k in st.session_state:
                    del st.session_state[k]

            st.rerun()    
    # 0번
    if page == "tab0":
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

            q_now = (st.session_state.get("tab0_search", "") or "").strip()
            print_msg = f"'{q_now}' 검색 결과: {len(filtered_df)}명" if q_now else ""

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
                    msg = f"'{q_now}' 검색 결과: {len(filtered_df)}명" if q_now else "&nbsp;"
                    st.markdown(
                        f"<div class='no-print' style='font-size:12px;color:#666;text-align:left;margin-top:-6px;min-height:18px;'>{msg}</div>",
                        unsafe_allow_html=True
                    )

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

            height = len(filtered_df) * 35 + 40
            st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=height)

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="print-area tab0-print-root">
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

    # 1번
    elif page == "tab1":
        st.markdown(print_banner, unsafe_allow_html=True)
        if not df.empty:
            col1, col2 = st.columns([3, 1])
            with col1:
                m1 = st.text_input("제목(연/월)", value=now_kst().strftime("%Y.%m"), key="m1")
            with col2:
                show_school_t1 = st.checkbox("학교명 표시", value=True, key="chk_school_m1")
                show_count_t1 = st.checkbox("학교별 인원수 표시", value=True, key="chk_count_m1")

            st.markdown(
                f"<div class='print-area'><div class='a4-print-box'><div class='report-view'>{generate_table1(df, show_school_t1, show_count_t1, m1)}</div></div></div>",
                unsafe_allow_html=True,
            )

    # 2번
    elif page == "tab2":
        st.markdown(print_banner, unsafe_allow_html=True)

        st.markdown("<div class='no-print'>", unsafe_allow_html=True)
        src_col1, src_col2 = st.columns([2.2, 3.8], vertical_alignment="bottom")
        with src_col1:
            table2_source_label = st.radio(
                "명단 선택",
                ["현재 명단", "다음달 명단"],
                horizontal=True,
                key="table2_source_label",
            )
        source_key = "current" if table2_source_label == "현재 명단" else "next"
        default_m2 = (
            now_kst().strftime("%Y-%m")
            if source_key == "current"
            else get_next_month_yyyy_mm()
        )
        m2_key = f"m2_{source_key}"
        with src_col2:
            m2 = st.text_input(
                "하단 표기",
                value=default_m2,
                key=m2_key,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        worksheet_name = WORKSHEET_STUDENTS if source_key == "current" else WORKSHEET_STUDENTS_NEXT
        df_table2 = load_data(worksheet_name)

        if not df_table2.empty:
            weekly_note_msg_key = f"weekly_note_msg_{source_key}"
            weekly_note_error_key = f"weekly_note_error_{source_key}"

            if st.session_state.get(weekly_note_msg_key) == "apply":
                st.success("인쇄에 반영되었습니다.")
                st.session_state.pop(weekly_note_msg_key, None)
            elif st.session_state.get(weekly_note_msg_key) == "save":
                st.success("저장 완료, 인쇄에 반영됩니다.")
                st.session_state.pop(weekly_note_msg_key, None)

            if st.session_state.get(weekly_note_error_key):
                st.error(st.session_state[weekly_note_error_key])
                st.session_state.pop(weekly_note_error_key, None)

            weekly_period_note_key = f"weekly_period_notes_{source_key}"
            if weekly_period_note_key not in st.session_state:
                try:
                    st.session_state[weekly_period_note_key] = load_weekly_period_notes(source=source_key)
                except Exception:
                    st.session_state[weekly_period_note_key] = {1: "", 2: "", 3: ""}

            chk_show_key = f"chk_show_period_notes_t2_{source_key}"
            selected_period_key = f"weekly_selected_period_note_{source_key}"

            if chk_show_key not in st.session_state:
                st.session_state[chk_show_key] = True
            if selected_period_key not in st.session_state:
                st.session_state[selected_period_key] = 1

            show_period_notes_t2 = st.session_state[chk_show_key]
            selected_period = st.session_state[selected_period_key]

            st.markdown(
                f"<div class='print-area'><div class='report-view'>{generate_table2(df_table2, m2, period_notes=st.session_state[weekly_period_note_key], show_period_notes=show_period_notes_t2)}</div></div>",
                unsafe_allow_html=True
            )

            st.markdown("<div class='no-print'>", unsafe_allow_html=True)

            left_col, right_col = st.columns([3.8, 2.2], vertical_alignment="bottom")
            with left_col:
                st.markdown(
                    """
                    <div class="weekly-note-header no-print" style="margin-top:14px; margin-bottom:6px; display:flex; align-items:baseline; gap:8px;">
                        <div style="font-weight:600; font-size:13px;">비고</div>
                        <div style="font-size:11px; color:#363636;">한 줄에 12자정도씩 입력해주세요</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with right_col:
                chk_col, select_col = st.columns([1.15, 1.0], vertical_alignment="bottom")
                with chk_col:
                    st.checkbox("비고칸 표시", key=chk_show_key)
                with select_col:
                    st.selectbox(
                        "교시 선택",
                        [1, 2, 3],
                        format_func=lambda x: f"{x}교시",
                        key=selected_period_key,
                        label_visibility="collapsed",
                    )

            show_period_notes_t2 = st.session_state[chk_show_key]
            selected_period = st.session_state[selected_period_key]

            with st.form(key=f"weekly_note_form_{source_key}", clear_on_submit=False):
                note_val = st.text_area(
                    "",
                    value=st.session_state[weekly_period_note_key].get(selected_period, ""),
                    key=f"weekly_period_note_input_{source_key}_{selected_period}",
                    height=260,
                    label_visibility="collapsed",
                )

                btn_apply, btn_save, btn_blank = st.columns([1, 1, 6])
                with btn_apply:
                    apply_clicked = st.form_submit_button("적용", use_container_width=True)
                with btn_save:
                    save_clicked = st.form_submit_button("저장", use_container_width=True, type="primary")

            st.markdown("</div>", unsafe_allow_html=True)

            if apply_clicked or save_clicked:
                merged_period_notes = dict(st.session_state[weekly_period_note_key])
                merged_period_notes[selected_period] = str(note_val).strip()
                st.session_state[weekly_period_note_key] = merged_period_notes

                if save_clicked:
                    try:
                        save_weekly_period_notes(st.session_state[weekly_period_note_key], source=source_key)
                        st.session_state[weekly_note_msg_key] = "save"
                    except Exception as e:
                        st.session_state[weekly_note_error_key] = f"저장 실패: {e}"
                else:
                    st.session_state[weekly_note_msg_key] = "apply"

                st.rerun()
        else:
            st.info(f"'{worksheet_name}' 워크시트에 데이터가 없습니다.")

    # 3번
    elif page == "tab3":
        st.markdown(print_banner, unsafe_allow_html=True)

        if not df.empty:
            st.markdown("<div id='t3-top'></div>", unsafe_allow_html=True)

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

            if "attendance_date_persist" not in st.session_state:
                st.session_state["attendance_date_persist"] = today_kst()

            d3 = st.date_input(
                "날짜 선택",
                value=st.session_state["attendance_date_persist"],
                key="attendance_date",
            )
            selected_date = d3
            st.session_state["attendance_date_persist"] = d3

            weekday = WEEKDAY_ORDER[selected_date.weekday()]
            date_key = selected_date.isoformat()

            save_lock_key = f"attendance_save_in_progress_{date_key}"
            is_saving = st.session_state.get(save_lock_key, False)

            if date_key not in st.session_state["assignments"]:
                try:
                    restored = load_attendance_for_date(date_key)
                    st.session_state["assignments"][date_key] = restored
                except Exception as e:
                    st.error(f"출석 데이터를 불러오지 못했습니다: {e}")
                    st.stop()

            day_store = st.session_state["assignments"][date_key]

            editor_version_key = f"attendance_editor_version_{date_key}"
            if editor_version_key not in st.session_state:
                st.session_state[editor_version_key] = 0
            editor_version = st.session_state[editor_version_key]

            summary_key = f"attendance_summary_{date_key}"
            if summary_key not in st.session_state:
                st.session_state[summary_key] = {}

            teacher_note_key = f"teacher_notes_{date_key}"
            if teacher_note_key not in st.session_state:
                try:
                    st.session_state[teacher_note_key] = load_teacher_notes_for_date(date_key)
                except Exception:
                    st.session_state[teacher_note_key] = {1: "", 2: "", 3: ""}

            preview_html_key = f"attendance_preview_html_{date_key}"
            preview_dirty_key = f"attendance_preview_dirty_{date_key}"
            status_msg_key = f"attendance_status_msg_{date_key}"
            summary_msg_key = f"attendance_summary_msg_{date_key}"

            if preview_dirty_key not in st.session_state:
                st.session_state[preview_dirty_key] = True
            if status_msg_key not in st.session_state:
                st.session_state[status_msg_key] = ""
            if summary_msg_key not in st.session_state:
                st.session_state[summary_msg_key] = ""

            day_mask = df[COL_DAYS].astype(str).apply(lambda x: weekday in split_days(x))
            df_day = df[day_mask].copy()
            df_day = df_day[df_day[COL_STATUS] == "재원"]

            grade_sort_map = {g: i for i, g in enumerate(GRADE_ORDER)}

            per_period_students = {}
            for p in [1, 2, 3]:
                df_p = filter_students_for_day_period(df_day, weekday, p).copy()
                df_p["_grade_order"] = df_p[COL_GRADE].map(grade_sort_map).fillna(999)
                df_p = df_p.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])
                per_period_students[p] = df_p

            st.markdown(
                f"""
                <div class="no-print section-nav-row">
                    <div>
                        <h3 style="margin:0;">📝 배정 · 결석 입력</h3>
                        <div style="font-size:12px; color:#666; margin-top:4px;">
                            작업 날짜 | {date_key} ({weekday})
                        </div>
                    </div>
                    <a href="#t3-preview" class="nav-btn">🖨️ 미리보기</a>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption("💡 배정: 알파벳 1글자 입력 (소문자 가능, 저장 시 대문자 변환) · 입력 후 Enter 또는 다른 칸 클릭 뒤 저장")

            summary_clicked = False
            save_clicked = False

            st.markdown("<div id='t3-editor'></div>", unsafe_allow_html=True)

            def build_period_summary(df_edited: pd.DataFrame | None) -> dict:
                if df_edited is None or df_edited.empty:
                    return {"total": 0, "absent": 0, "letters": {}}

                total = len(df_edited)
                absent = int(df_edited["결석"].fillna(False).astype(bool).sum())

                letters = {}
                for _, row in df_edited.iterrows():
                    row_absent = bool(row["결석"])
                    if row_absent:
                        continue

                    letter = sanitize_letter(row["배정"])
                    if letter:
                        letters[letter] = letters.get(letter, 0) + 1

                return {
                    "total": total,
                    "absent": absent,
                    "letters": dict(sorted(letters.items()))
                }

            summary_data = st.session_state.get(summary_key, {})
            status_msg = st.session_state.get(status_msg_key, "")
            summary_msg = st.session_state.get(summary_msg_key, "")
            status_text = status_msg or "최근 저장 | —"

            st.markdown("<div class='no-print'>", unsafe_allow_html=True)
            if is_saving:
                st.info("저장 중입니다. 새로고침하거나 날짜를 바꾸지 말고 잠시 기다려 주세요.")
            else:
                st.success(status_text)
            st.markdown("</div>", unsafe_allow_html=True)

            if summary_msg:
                st.caption(summary_msg)

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

            with st.form(key=f"assign_form_{date_key}_{editor_version}", clear_on_submit=False):
                has_p1 = not per_period_students.get(1, pd.DataFrame()).empty
                has_p2 = not per_period_students.get(2, pd.DataFrame()).empty
                has_p3 = not per_period_students.get(3, pd.DataFrame()).empty

                btn_summary, btn_save, btn_blank = st.columns([1.2, 1.2, 8.6])

                with btn_summary:
                    summary_clicked = st.form_submit_button(
                        "합계",
                        use_container_width=True,
                        disabled=is_saving,
                    )
                with btn_save:
                    save_clicked = st.form_submit_button(
                        "저장 중..." if is_saving else "저장",
                        use_container_width=True,
                        type="primary",
                        disabled=is_saving,
                    )

                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

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
                            else:
                                c_let = sanitize_letter(current.get("letter", ""))
                                c_abs = bool(current.get("absent", False))

                            school = str(row[COL_SCHOOL]).strip()
                            grade = str(row[COL_GRADE]).strip()
                            school_grade = school + (grade[1:] if school and grade and school[-1] == grade[0] else grade)
                            student_memo = str(row.get(COL_STUDENT_MEMO, "")).strip()

                            editor_data.append({
                                "_skey": skey,
                                "이름": f"{row[COL_NAME]} ({school_grade})",
                                "메모": student_memo,
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
                                "메모": st.column_config.TextColumn("메모", disabled=True, width="small"),
                                "배정": st.column_config.TextColumn("배정", max_chars=1, width="small"),
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

                st.markdown(
                    """
                    <div class="no-print" style="margin-top:12px; margin-bottom:8px;">
                        <h4 style="margin:0 0 6px 0; font-size:14px;">메모</h4>
                        <div style="font-size:12px; color:#666;">한 줄에 8~10자 정도 입력</div>
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

            if summary_clicked:
                summary_result = {}
                for p in [1, 2, 3]:
                    df_edited = edited_dfs.get(p)
                    summary_result[p] = build_period_summary(df_edited)
                st.session_state[summary_key] = summary_result
                st.session_state[summary_msg_key] = f"합계 갱신 완료 | {now_kst().strftime('%H:%M:%S')}"
                st.rerun()

            if save_clicked:
                if st.session_state.get(save_lock_key, False):
                    st.stop()

                st.session_state[save_lock_key] = True
                st.session_state[summary_msg_key] = ""

                try:
                    new_day_store = {}
                    for p in [1, 2, 3]:
                        df_edited = edited_dfs.get(p)
                        if df_edited is None or df_edited.empty:
                            continue

                        for _, row in df_edited.iterrows():
                            skey = row["_skey"]
                            letter = sanitize_letter(row["배정"])
                            absent = bool(row["결석"])

                            if absent:
                                letter = ""

                            if letter or absent:
                                new_day_store[(p, skey)] = {
                                    "letter": letter,
                                    "absent": absent,
                                }

                    summary_result = {}
                    for p in [1, 2, 3]:
                        df_edited = edited_dfs.get(p)
                        summary_result[p] = build_period_summary(df_edited)
                    st.session_state[summary_key] = summary_result

                    new_teacher_notes = {
                        1: str(note_1).strip(),
                        2: str(note_2).strip(),
                        3: str(note_3).strip(),
                    }

                    st.session_state["assignments"][date_key] = new_day_store
                    day_store = st.session_state["assignments"][date_key]
                    st.session_state[teacher_note_key] = new_teacher_notes

                    save_attendance_for_date(date_key, new_day_store)
                    save_teacher_notes_for_date(date_key, new_teacher_notes)

                    st.session_state[preview_dirty_key] = True
                    st.session_state[preview_html_key] = generate_table3(
                        df,
                        selected_date,
                        False,
                        day_store,
                        st.session_state.get(teacher_note_key, {1: "", 2: "", 3: ""}),
                    )

                    saved_time = now_kst().strftime('%H:%M:%S')
                    st.session_state[preview_dirty_key] = False
                    st.session_state[status_msg_key] = f"저장 완료 | {date_key} {saved_time}"
                    st.session_state[summary_msg_key] = ""
                    st.rerun()

                except Exception as e:
                    st.error(f"🚨 저장 실패: {e}")
                finally:
                    st.session_state[save_lock_key] = False

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

            st.markdown("<div id='t3-preview'></div>", unsafe_allow_html=True)

            if preview_html_key not in st.session_state or st.session_state.get(preview_dirty_key, True):
                st.session_state[preview_html_key] = generate_table3(
                    df,
                    selected_date,
                    False,
                    day_store,
                    st.session_state.get(teacher_note_key, {1: "", 2: "", 3: ""}),
                )
                st.session_state[preview_dirty_key] = False

            preview_html = st.session_state[preview_html_key]

            st.markdown(
                f"<div class='print-area'><div class='a4-print-box'><div class='report-view'>{preview_html}</div></div></div>",
                unsafe_allow_html=True
            )

            st.markdown("<div id='t3-bottom'></div>", unsafe_allow_html=True)

            st.markdown(
                """
                <div class="no-print" style="display:flex; justify-content:flex-end; gap:10px; margin-top:15px; margin-bottom:20px;">
                    <a href="#t3-editor" class="nav-btn">✏️ 입력창으로</a>
                    <a href="#t3-preview" class="nav-btn">🖨️ 미리보기</a>
                </div>
                """,
                unsafe_allow_html=True
            )
    # 4번
    elif page == "tab4":
        st.markdown(print_banner, unsafe_allow_html=True)
        if not df.empty:
            m4 = st.text_input("제목(연/월)", value=now_kst().strftime("%Y.%m"), key="m4")
            st.markdown(
                f"<div class='print-area'><div class='a4-print-box'><div class='report-view'>{generate_table4(df, True, m4)}</div></div></div>",
                unsafe_allow_html=True
            )

