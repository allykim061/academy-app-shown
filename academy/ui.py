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
from .utils import get_student_key, sanitize_letter, now_kst, today_kst, split_days
from .backup import save_attendance_for_date, load_attendance_for_date

def run_app():
    df = load_data()

    print_banner = (
        '<div class="no-print" style="background-color:#f1f3f5;padding:15px;border-radius:8px;'
        'border-left:5px solid #868396;margin-bottom:20px;">🖨️ 인쇄: 우측 상단 ⋮ ➜ Print 선택</div>'
    )

    # ✅ 배정 저장소(session_state)
    if "assignments" not in st.session_state:
        st.session_state["assignments"] = {}  # {date_iso: {(period, student_key): "A"}}

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
            m2 = st.text_input("하단 표기", value=now_kst().strftime("%Y-%m"), key="m2")
            st.markdown(f"<div class='a4-print-box'><div class='report-view'>{generate_table2(df, m2)}</div></div>", unsafe_allow_html=True)

    # 탭 3
    with tab_list[3]:
        st.markdown(print_banner, unsafe_allow_html=True)

        if not df.empty:
            # 기본 날짜
            d3 = st.date_input("날짜 선택", value=today_kst())

            weekday = WEEKDAY_ORDER[d3.weekday()]
            date_key = d3.isoformat()

            # 날짜별 저장 데이터 1회 자동 복구
            try:
                restored = load_attendance_for_date(date_key)
                st.session_state["assignments"][date_key] = restored
            except Exception:
                st.session_state["assignments"].setdefault(date_key, {})

            day_store = st.session_state["assignments"].setdefault(date_key, {})

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

            # 배정/결석 입력 UI
            with st.expander("📝 배정, 결석 입력", expanded=False):
                st.caption("💡 배정: 알파벳 1글자 입력 · Enter / 방향키 이동")

                apply_clicked = False
                save_clicked = False
                reset_clicked = False

                with st.form(key=f"assign_form_{date_key}", clear_on_submit=False):
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

                                editor_data.append({
                                    "_skey": skey,
                                    "이름": f"{row[COL_NAME]} ({row[COL_SCHOOL]} {row[COL_GRADE]})",
                                    "배정": c_let,
                                    "결석": c_abs,
                                })

                            df_editor = pd.DataFrame(editor_data)
                            dynamic_height = (len(df_editor) * 35) + 40

                            edited_df = st.data_editor(
                                df_editor,
                                height=dynamic_height,
                                column_config={
                                    "_skey": None,
                                    "이름": st.column_config.TextColumn("이름", disabled=True),
                                    "배정": st.column_config.TextColumn("배정", max_chars=1),
                                    "결석": st.column_config.CheckboxColumn("결석"),
                                },
                                hide_index=True,
                                key=f"editor_{date_key}_{p}",
                                use_container_width=True,
                            )
                            return edited_df

                    edited_dfs[1] = render_data_editor(ec1, 1)
                    edited_dfs[2] = render_data_editor(ec2, 2)
                    edited_dfs[3] = render_data_editor(ec3, 3)

                    btn_apply, btn_save, btn_reset, btn_blank = st.columns([1, 1, 1, 7])
                    with btn_apply:
                        apply_clicked = st.form_submit_button("적용", use_container_width=True)
                    with btn_save:
                        save_clicked = st.form_submit_button(
                            "저장",
                            use_container_width=True,
                            type="primary"
                        )
                    with btn_reset:
                        reset_clicked = st.form_submit_button("초기화", use_container_width=True)

                # 초기화: 현재 화면 입력만 비움
                if reset_clicked:
                    st.session_state["assignments"][date_key] = {}
                    st.rerun()

                # 적용 / 저장: 현재 편집값을 day_store에 반영
                if apply_clicked or save_clicked:
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

                    st.success("출석부에 반영되었습니다.")

                # 저장: 반영 + 구글 시트 저장
                if save_clicked:
                    try:
                        save_attendance_for_date(date_key, day_store)
                        st.success("배정/결석 데이터가 저장되었습니다.")
                    except Exception as e:
                        st.error(f"저장 실패: {e}")

            # 출석부 표 렌더링 (항상 표시)
            st.markdown(
                f"<div class='a4-print-box'><div class='report-view'>{generate_table3(df, d3, False, day_store)}</div></div>",
                unsafe_allow_html=True
            )

    # 탭 4
    with tab_list[4]:
        st.markdown(print_banner, unsafe_allow_html=True)
        if not df.empty:
            m4 = st.text_input("제목(연/월)", value=now_kst().strftime("%Y.%m"), key="m4")
            st.markdown(f"<div class='a4-print-box'><div class='report-view'>{generate_table4(df, True, m4)}</div></div>", unsafe_allow_html=True)