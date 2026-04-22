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
from .utils import get_student_key, sanitize_letter, now_kst, today_kst, split_days, match_attendance
from .backup import (
    save_attendance_for_date, load_attendance_for_date,
    save_teacher_notes_for_date, load_teacher_notes_for_date,
    save_weekly_period_notes, load_weekly_period_notes,
)

def run_app():
    df = load_data()

    print_banner = (
        '<div class="no-print" style="background-color:#f1f3f5;padding:15px;border-radius:8px;'
        'border-left:5px solid #868396;margin-bottom:20px;">🖨️ 인쇄: 우측 상단 ⋮ ➜ Print 선택</div>'
    )

    # ✅ 배정 저장소(session_state)
    if "assignments" not in st.session_state:
        st.session_state["assignments"] = {}  # {date_iso: {(period, student_key): {"letter": "", "absent": False}}}

    # 사이드바
    with st.sidebar:
        print_orientation = st.radio("용지 방향", ["세로", "가로"])
        st.markdown(get_print_css_cached(print_orientation), unsafe_allow_html=True)

        if st.button("새로고침"):
            st.cache_data.clear()

            for k in list(st.session_state.keys()):
                if k.startswith("preview_html_") or k.startswith("attendance_editor_version_"):
                    del st.session_state[k]

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

                    st.markdown(
                        f"<div class='no-print' style='font-size:12px;color:#666;text-align:left;margin-top:-6px;min-height:18px;'>{msg}</div>",
                        unsafe_allow_html=True
                    )

            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

            height = len(filtered_df) * 35 + 40
            st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=height)

            st.markdown("</div>", unsafe_allow_html=True)

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
        # 탭 2는 선택된 워크시트 기준으로 별도 로드
        st.markdown("<div class='no-print'>", unsafe_allow_html=True)
        src_col1, src_col2 = st.columns([2.2, 3.8], vertical_alignment="bottom")
        with src_col1:
            table2_source_label = st.radio(
                "명단 선택",
                ["현재 명단", "다음달 예정"],
                horizontal=True,
                key="table2_source_label",
            )
        with src_col2:
            m2 = st.text_input("하단 표기", value=now_kst().strftime("%Y-%m"), key="m2")
        st.markdown("</div>", unsafe_allow_html=True)
        source_key = "current" if table2_source_label == "현재 명단" else "next"
        worksheet_name = WORKSHEET_STUDENTS if source_key == "current" else WORKSHEET_STUDENTS_NEXT
        df_table2 = load_data(worksheet_name)
        if not df_table2.empty:
            # source별 알림 메시지
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
            # source별 교시 비고 저장값 로드
            weekly_period_note_key = f"weekly_period_notes_{source_key}"
            if weekly_period_note_key not in st.session_state:
                try:
                    st.session_state[weekly_period_note_key] = load_weekly_period_notes(source=source_key)
                except Exception:
                    st.session_state[weekly_period_note_key] = {1: "", 2: "", 3: ""}
            # 체크박스 / selectbox 기본값도 source별 분리
            chk_show_key = f"chk_show_period_notes_t2_{source_key}"
            selected_period_key = f"weekly_selected_period_note_{source_key}"
            if chk_show_key not in st.session_state:
                st.session_state[chk_show_key] = True
            if selected_period_key not in st.session_state:
                st.session_state[selected_period_key] = 1
            show_period_notes_t2 = st.session_state[chk_show_key]
            selected_period = st.session_state[selected_period_key]
            # 1) HTML 미리보기
            st.markdown(
                f"<div class='report-view'>{generate_table2(df_table2, m2, period_notes=st.session_state[weekly_period_note_key], show_period_notes=show_period_notes_t2)}</div>",
                unsafe_allow_html=True
            )
            # 2) 아래부터 입력 UI만 인쇄 제외
            st.markdown("<div class='no-print'>", unsafe_allow_html=True)
            # 3) 한 줄 헤더: [비고 | 설명]   [비고칸 표시 | selectbox]
            left_col, right_col = st.columns([3.8, 2.2], vertical_alignment="bottom")
            with left_col:
                title_text = "비고"
                sub_text = "한 줄에 12자정도씩 입력해주세요"
                st.markdown(
                    f"""
                    <div class="weekly-note-header no-print" style="margin-top:14px; margin-bottom:6px; display:flex; align-items:baseline; gap:8px;">
                        <div style="font-weight:600; font-size:13px;">{title_text}</div>
                        <div style="font-size:11px; color:#363636;">{sub_text}</div>
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
            # 최신 상태값 다시 읽기
            show_period_notes_t2 = st.session_state[chk_show_key]
            selected_period = st.session_state[selected_period_key]
            # 4) 입력칸 + 버튼
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

    # 탭 3
    with tab_list[3]:
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

            d3 = st.date_input("날짜 선택", value=today_kst())
            weekday = WEEKDAY_ORDER[d3.weekday()]
            date_key = d3.isoformat()

            if date_key not in st.session_state["assignments"]:
                try:
                    restored = load_attendance_for_date(date_key)
                    st.session_state["assignments"][date_key] = restored
                except Exception:
                    st.session_state["assignments"][date_key] = {}

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

            with st.form(key=f"assign_form_{date_key}_{editor_version}", clear_on_submit=False):
                has_p1 = not per_period_students.get(1, pd.DataFrame()).empty
                has_p2 = not per_period_students.get(2, pd.DataFrame()).empty
                has_p3 = not per_period_students.get(3, pd.DataFrame()).empty

                btn_summary, btn_save, btn_blank = st.columns([1.2, 1.2, 8.6])

                with btn_summary:
                    summary_clicked = st.form_submit_button("합계", use_container_width=True)

                with btn_save:
                    save_clicked = st.form_submit_button("저장", use_container_width=True, type="primary")

                apply_clicked = False
                reset_clicked = False
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

            if summary_clicked:
                summary_result = {}
                for p in [1, 2, 3]:
                    df_edited = edited_dfs.get(p)
                    summary_result[p] = build_period_summary(df_edited)
                st.session_state[summary_key] = summary_result

            if save_clicked:
                for p in [1, 2, 3]:
                    df_edited = edited_dfs.get(p)
                    if df_edited is not None and not df_edited.empty:
                        for _, row in df_edited.iterrows():
                            skey = row["_skey"]
                            v_let = row["배정"]
                            v_abs = row["결석"]

                            day_store[(p, skey)] = {
                                "letter": sanitize_letter(v_let),
                                "absent": bool(v_abs),
                            }

                st.success("저장 완료, 인쇄에 반영됩니다.")

                summary_result = {}
                for p in [1, 2, 3]:
                    df_edited = edited_dfs.get(p)
                    summary_result[p] = build_period_summary(df_edited)
                st.session_state[summary_key] = summary_result

            if save_clicked:
                st.session_state[teacher_note_key] = {
                    1: str(note_1).strip(),
                    2: str(note_2).strip(),
                    3: str(note_3).strip(),
                }

            if save_clicked:
                try:
                    save_attendance_for_date(date_key, day_store)
                    save_teacher_notes_for_date(date_key, st.session_state[teacher_note_key])
                    st.success("저장 완료")
                except Exception as e:
                    st.error(f"저장 실패: {e}")

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

            preview_html = generate_table3(
                df,
                d3,
                False,
                day_store,
                st.session_state.get(teacher_note_key, {1: "", 2: "", 3: ""}),
            )

            st.markdown(
                f"<div class='a4-print-box'><div class='report-view'>{preview_html}</div></div>",
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

    # 탭 4
    with tab_list[4]:
        st.markdown(print_banner, unsafe_allow_html=True)
        if not df.empty:
            m4 = st.text_input("제목(연/월)", value=now_kst().strftime("%Y.%m"), key="m4")
            st.markdown(f"<div class='a4-print-box'><div class='report-view'>{generate_table4(df, True, m4)}</div></div>", unsafe_allow_html=True)