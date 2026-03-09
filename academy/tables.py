# academy/tables.py
import pandas as pd

from .config import (
    COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS,
    GRADE_ORDER, WEEKDAY_ORDER
)
from .utils import split_days, extract_period_numbers, match_attendance, get_student_key, sanitize_letter
from .filters import filter_students_for_day_period

GRADE_SORT_MAP = {str(g).strip(): i for i, g in enumerate(GRADE_ORDER)}


def get_school_rank(school_name: str) -> int:
    name = str(school_name).strip()
    if not name:
        return 99
    if name.endswith("초"):
        return 1
    if name.endswith("중"):
        return 2
    if name.endswith("고"):
        return 3
    return 4


def format_grouped_names(
    group_df: pd.DataFrame,
    key_col: str,
    name_col: str,
    show_key: bool,
    show_count: bool,
    key_wrapper: callable,
    spacer: str = " "
) -> str:
    formatted_groups = []

    for key, sub_group in group_df.groupby(key_col, sort=False):
        names_list = sub_group[name_col].tolist()
        names_str = " ".join(names_list)
        count = len(names_list)

        key_text = key_wrapper(key) if show_key else ""
        count_text = f" {count}명" if (show_count and count >= 4) else ""

        if count == 1:
            formatted_groups.append(f"{key_text}{names_str}{count_text}")
        else:
            formatted_groups.append(f"{key_text}[{names_str}]{count_text}")

    return spacer.join(formatted_groups)


def generate_total_list_html(df: pd.DataFrame) -> str:
    html = "<table class='total-list-table' style='width:100%;'><thead><tr>"
    cols = [COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS]
    widths = {COL_NAME: "15%", COL_SCHOOL: "25%", COL_GRADE: "10%", COL_DAYS: "20%", COL_PERIOD: "20%", COL_STATUS: "10%"}

    for c in cols:
        w = widths.get(c, "15%")
        html += f"<th style='width:{w};'>{c}</th>"
    html += "</tr></thead><tbody>"

    for r in df.to_dict("records"):
        html += "<tr>"
        for c in cols:
            html += f"<td>{r[c]}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def generate_table1(df: pd.DataFrame, show_school: bool, show_count: bool, month_text: str) -> str:
    df_active = df[df[COL_STATUS] == "재원"].copy()
    html = f"<h2 style='text-align:center; font-size:16pt;'>학년별 명단 ({month_text})</h2>"
    
    html += "<table class='table1-custom'><thead><tr><th>학년</th><th>학생 명단</th><th>인원수</th></tr></thead><tbody>"

    total = 0
    for grade in GRADE_ORDER:
        group = df_active[df_active[COL_GRADE] == grade]
        if group.empty:
            continue

        group_sorted = group.sort_values(by=[COL_SCHOOL, COL_NAME])

        if show_school or show_count:
            names_final_str = format_grouped_names(
                group_sorted,
                key_col=COL_SCHOOL,
                name_col=COL_NAME,
                show_key=show_school,
                show_count=show_count,
                key_wrapper=lambda school: f"【{school}】",
                spacer="&nbsp;&nbsp;&nbsp;&nbsp;"
            )
        else:
            names_final_str = " ".join(group_sorted[COL_NAME].tolist())

        html += f"<tr><th>{grade}</th><td class='t1-names'>{names_final_str}</td><td>{len(group)}</td></tr>"
        total += len(group)

    # --- 주 N회 합계 요약 부분 ---
    df_active["days_count"] = df_active[COL_DAYS].apply(lambda x: len(split_days(x)))
    summary_texts = []

    def get_summary_str(count_target, label, is_show_school, is_show_count):
        df_target = df_active[df_active["days_count"] == count_target].sort_values(by=[COL_SCHOOL, COL_NAME])
        if df_target.empty:
            return ""

        if is_show_school or is_show_count:
            body = format_grouped_names(
                df_target,
                key_col=COL_SCHOOL,
                name_col=COL_NAME,
                show_key=is_show_school,
                show_count=is_show_count,
                key_wrapper=lambda school: f"【{school}】",
                spacer=" "
            )
        else:
            groups = []
            for _, school_group in df_target.groupby(COL_SCHOOL, sort=False):
                groups.append(" ".join(school_group[COL_NAME].tolist()))
            body = " ".join(groups)

        return f"<div class='t1-summary-line'><strong>{label}:</strong> {body}</div>"

    str_1day = get_summary_str(1, "주 1회", show_school, show_count)
    str_3day = get_summary_str(3, "주 3회", show_school, show_count)

    if str_1day: summary_texts.append(str_1day)
    if str_3day: summary_texts.append(str_3day)

    summary_final_str = "".join(summary_texts)
    
    html += f"<tr><th>합계</th><td class='t1-names t1-summary'>{summary_final_str}</td><td>{total}</td></tr></tbody></table>"
    return html


def generate_table2(df: pd.DataFrame, month_text: str) -> str:
    df_active = df[df[COL_STATUS] == "재원"].copy()
    html = f"<h2 class='no-print' style='text-align:center; font-size:16pt;'>{month_text} 반편성 내역</h2>"
    target_days = ["월", "화", "수", "목"]

    periods_set = set()
    for p_str in df_active[COL_PERIOD]:
        for n in extract_period_numbers(p_str):
            if n > 0:
                periods_set.add(n)
    periods = sorted(periods_set) if periods_set else [1, 2, 3]

    # ✅ 학년 정렬용 딕셔너리

    for p in periods:
        html += "<div class='a4-print-box'><table class='weekly-table'><thead><tr>"
        html += "<th style='width:10%;'>수업시간</th>"
        for d in target_days:
            html += f"<th style='width:20%;'>{d}</th>"
        html += "<th style='width:10%;'>비고</th></tr></thead><tbody>"
        
        # ✅ 수정 1: 인라인 스타일을 지우고 'period-cell' 클래스만 부여 (CSS가 중앙 정렬 담당)
        html += f"<tr><td class='period-cell'>{p}교시</td>"

        for d in target_days:
            condition = df_active.apply(
                lambda row: match_attendance(row[COL_DAYS], row[COL_PERIOD], d, p), 
                axis=1
            )
            students = df_active[condition].copy()

            student_list = []
            last_grade = None

            if not students.empty:
                # 학년(GRADE_ORDER) -> 학교 -> 이름 정렬
                students["_grade_order"] = students[COL_GRADE].astype(str).str.strip().map(GRADE_SORT_MAP).fillna(999)
                students = students.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])

                for _, r in students.iterrows():
                    grade = str(r[COL_GRADE]).strip()

                   # 학년 바뀌면 띄우기
                    if last_grade is not None and grade != last_grade:
                        # 💡 &nbsp;(빈 줄)를 지우고 height로 조정
                        student_list.append("<div style='height: 8px;'></div>")

                    s_str, g_str = str(r[COL_SCHOOL]).strip(), grade
                    school_grade = s_str + (g_str[1:] if s_str and g_str and s_str[-1] == g_str[0] else g_str)

                    student_list.append(
                        f"<div class='weekly-name' style='text-align:left;'>{r[COL_NAME]} ({school_grade})</div>"
                    )
                    last_grade = grade

            # 총 인원수
            count_html = (
                f"<div class='weekly-name' style='text-align:left; font-weight:bold; margin-top:4px;'>{len(students)}명</div>"
                if len(students) > 0 else ""
            )

            # ✅ 수정 2: 스타일 코드를 최소화 (vertical-align 등은 CSS에서 처리)
            html += (
                f"<td style='text-align:left !important;'>"
                f"{''.join(student_list)}{count_html}</td>"
            )

        html += f"<td></td></tr></tbody></table><div class='date-footer'>{month_text}</div></div>"
        
    return html


def generate_table3(df: pd.DataFrame, target_date, include_paused: bool, assignment_map: dict) -> str:
    weekday = WEEKDAY_ORDER[target_date.weekday()]
    day_mask = df[COL_DAYS].astype(str).apply(lambda x: weekday in split_days(x))
    df_day = df[day_mask].copy()

    if not include_paused:
        df_day = df_day[df_day[COL_STATUS] == "재원"]

    # ✅ 제목 (inline 유지: 기존과 동일)
    html = (
        f"<h2 class='t3-title' style='text-align:left; font-size:16pt; border-bottom:2px solid black;"
        f" padding-bottom:5px; margin:0 0 8px 0;'>"
        f"{target_date.month}-{target_date.day} {weekday}</h2>"
    )
    html += "<div class='daily-grid-container'>"

    # -----------------------------
    # 1) 각 교시 rows[p] 만들기
    # -----------------------------
    rows = {1: [], 2: [], 3: []}

    for p in [1, 2, 3]:
        df_p = filter_students_for_day_period(df_day, weekday, p)
        if df_p.empty:
            # 교시가 아예 없으면 빈 표를 만들긴 하되, 헤더/마감선 구조는 유지
            rows[p] = []
            continue

        df_p["_grade_order"] = (
            df_p[COL_GRADE]
            .astype(str)
            .str.strip()
            .map(GRADE_SORT_MAP)
            .fillna(999)
        )
        df_p = df_p.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])

        last_grade = None
        p_count, p_absent = 0, 0
        p_alpha_counts = {}

        # 학생 행
        for _, row in df_p.iterrows():
            grade = str(row[COL_GRADE]).replace("\u00A0", "").replace("\u3000", "").strip()
            is_new_grade = (last_grade is not None and grade != last_grade)

            pause = " (휴)" if row[COL_STATUS] == "휴원" else ""
            s_str = str(row[COL_SCHOOL]).strip()
            school_grade = s_str + (grade[1:] if s_str and grade and s_str[-1] == grade[0] else grade)
            name_text = f"{row[COL_NAME]} ({school_grade}){pause}"

            skey = get_student_key(row)
            akey = (p, skey)

            data = assignment_map.get(akey, {"letter": "", "absent": False})
            if not isinstance(data, dict):
                data = {"letter": sanitize_letter(str(data)), "absent": False}

            letter = sanitize_letter(data.get("letter", ""))
            is_abs = bool(data.get("absent", False))

            if is_abs:
                p_absent += 1
            else:
                p_count += 1
                if letter:
                    p_alpha_counts[letter] = p_alpha_counts.get(letter, 0) + 1

            rows[p].append({
                "type": "student",
                "name_text": name_text,
                "letter": letter,
                "is_abs": is_abs,
                "is_new_grade": is_new_grade,
            })

            last_grade = grade

        # 요약(집계) — “한 줄=한 행”
        total_in_period = p_count + p_absent
        if total_in_period > 0:
            summary_lines = []
            if p_count > 0:
                summary_lines.append(f"{p_count}명")
            for L in sorted(p_alpha_counts.keys()):
                summary_lines.append(f"{L} : {p_alpha_counts[L]}명")
            if p_absent > 0:
                summary_lines.append(
                    f"<span style='color:#d9534f; font-weight:600;'>결석 : {p_absent}명</span>"
                )

            if summary_lines:
                # ✅ colspan 금지: 4칸 gap으로 세로선 유지
                rows[p].append({"type": "gap"})
                for line_text in summary_lines:
                    rows[p].append({"type": "summary", "text": line_text})

    # -----------------------------
    # 2) max_len 구해서 blank padding
    # -----------------------------
    max_len = max(len(rows[1]), len(rows[2]), len(rows[3])) if not df_day.empty else 0

    for p in [1, 2, 3]:
        while len(rows[p]) < max_len:
            rows[p].append({"type": "blank"})
        # ✅ 마지막 마감선은 “각 교시 표에 1번씩만” (모양 정합성 위해)
        rows[p].append({"type": "bottom"})

    # -----------------------------
    # 3) 렌더링(각 교시 표 독립)
    # -----------------------------
    # ✅ 헤더 폭: 출석/숙제/배정이 답답하면 여기서 더 넓힘
    th_name = "66%"
    th_small = "11.33%"  # 3개 합이 34% = 66 + 34 = 100

    for p in [1, 2, 3]:
        html += "<div class='period-column'>"
        html += "<table class='table3-custom daily-table'><thead><tr>"
        html += (
            f"<th style='width:{th_name};'>{p}교시</th>"
            f"<th style='width:{th_small};'>출석</th>"
            f"<th style='width:{th_small};'>숙제</th>"
            f"<th style='width:{th_small};'>배정</th>"
        )
        html += "</tr></thead><tbody>"

        for item in rows[p]:
            t = item.get("type")

            if t == "student":
                abs_class = " absent" if item.get("is_abs") else ""
                gap_class = " new-grade-gap" if item.get("is_new_grade") else ""
                name_text = item.get("name_text", "")
                letter = item.get("letter", "")

                html += (
                    "<tr class='t3-row'>"
                    f"<td class='name-cell{abs_class}'><div class='student-inner{gap_class}'>{name_text}</div></td>"
                    f"<td><div class='student-inner{gap_class}'><div class='check-box'></div></div></td>"
                    f"<td><div class='student-inner{gap_class}'><div class='check-box'></div></div></td>"
                    f"<td class='assign-cell'><div class='student-inner{gap_class}'>{letter}</div></td>"
                    "</tr>"
                )

            elif t == "summary":
                text = item.get("text", "")
                html += (
                    "<tr class='t3-row'>"
                    f"<td class='summary-cell'>{text}</td>"
                    "<td></td><td></td><td></td>"
                    "</tr>"
                )

            elif t == "gap":
                html += (
                    "<tr class='t3-gap-row'>"
                    "<td class='t3-gap'>&nbsp;</td>"
                    "<td class='t3-gap'>&nbsp;</td>"
                    "<td class='t3-gap'>&nbsp;</td>"
                    "<td class='t3-gap'>&nbsp;</td>"
                    "</tr>"
                )

            elif t == "blank":
                # ✅ 빈칸 찌그러짐 방지: &nbsp;
                html += (
                    "<tr class='t3-row t3-blank-row'>"
                    "<td class='t3-blank'>&nbsp;</td>"
                    "<td class='t3-blank'>&nbsp;</td>"
                    "<td class='t3-blank'>&nbsp;</td>"
                    "<td class='t3-blank'>&nbsp;</td>"
                    "</tr>"
                )

            elif t == "bottom":
                html += (
                    "<tr class='t3-bottom'>"
                    "<td></td><td></td><td></td><td></td>"
                    "</tr>"
                )

        html += "</tbody></table></div>"

    html += "</div>"  # daily-grid-container end
    return html
    
def generate_table4(df: pd.DataFrame, show_grade: bool, month_text: str) -> str:
    df_active = df[df[COL_STATUS] == "재원"].copy()
    
    # ✅ 1) 학교 이름 추출 후 [1순위: 학교급(초/중/고), 2순위: 가나다순] 정렬
    unique_schools = df_active[COL_SCHOOL].dropna().unique().tolist()
    unique_schools.sort(key=lambda x: (get_school_rank(x), str(x)))

    # 학년 정렬 기준표 (GRADE_ORDER: 초1 -> 초2 -> ... 고3)
    html = f"<h2 style='text-align:center; font-size:16pt;'>학교별 명단 ({month_text})</h2>"
    
    # 1번 표의 비율(8%, 84%, 8%)과 큼직한 글자 스타일(table1-custom)유지, 첫번째 비율은 변경
    html += "<table class='table1-custom table4-custom'><thead><tr><th>학교</th><th>학생 명단</th><th>인원수</th></tr></thead><tbody>"
    
    total = 0
    for school in unique_schools:
        group = df_active[df_active[COL_SCHOOL] == school].copy()
        if group.empty:
            continue

        # 데이터에 묻어있는 공백 찌꺼기 청소
        group["_grade_clean"] = group[COL_GRADE].astype(str).str.strip()

        # [같은 학교 내 정렬] 1순위: 학년 순서, 2순위: 이름 가나다순
        group["_grade_order"] = group["_grade_clean"].map(GRADE_SORT_MAP).fillna(999)
        group_sorted = group.sort_values(by=["_grade_order", COL_NAME])

        if show_grade:
            names_final_str = format_grouped_names(
                group_sorted,
                key_col="_grade_clean",
                name_col=COL_NAME,
                show_key=True,
                show_count=True,
                key_wrapper=lambda grade: f"【{grade}】 ",
                spacer="&nbsp;&nbsp;&nbsp;&nbsp;"
            )
        else:
            names_final_str = " ".join(group_sorted[COL_NAME].tolist())

        # t1-names 클래스를 적용해 좌상단 정렬과 행간 띄우기 적용
        html += f"<tr><th>{school}</th><td class='t1-names'>{names_final_str}</td><td>{len(group)}</td></tr>"
        total += len(group)

    # 합계 칸
    html += f"<tr><th>합계</th><td class='t1-names'></td><td>{total}</td></tr></tbody></table>"
    
    return html