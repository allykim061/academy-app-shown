# academy/tables.py
import pandas as pd

from .config import (
    COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS,
    COL_STUDENT_MEMO,
    GRADE_ORDER, WEEKDAY_ORDER
)
from .utils import (
    split_days, extract_period_numbers, match_attendance,
    get_student_key, sanitize_letter, safe_html_text
)
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
        names_list = [safe_html_text(x) for x in sub_group[name_col].tolist()]
        names_str = " ".join(names_list)
        count = len(names_list)

        safe_key = safe_html_text(key)
        key_text = key_wrapper(safe_key) if show_key else ""
        count_text = f" {count}명" if (show_count and count >= 4) else ""

        if count == 1:
            formatted_groups.append(f"{key_text}{names_str}{count_text}")
        else:
            formatted_groups.append(f"{key_text}[{names_str}]{count_text}")

    return spacer.join(formatted_groups)


def generate_total_list_html(df: pd.DataFrame) -> str:
    html = "<table class='total-list-table' style='width:100%;'><thead><tr>"
    cols = [COL_NAME, COL_SCHOOL, COL_GRADE, COL_DAYS, COL_PERIOD, COL_STATUS]
    widths = {
        COL_NAME: "15%",
        COL_SCHOOL: "25%",
        COL_GRADE: "10%",
        COL_DAYS: "20%",
        COL_PERIOD: "20%",
        COL_STATUS: "10%"
    }

    for c in cols:
        w = widths.get(c, "15%")
        html += f"<th style='width:{w};'>{c}</th>"
    html += "</tr></thead><tbody>"

    for r in df.to_dict("records"):
        html += "<tr>"
        for c in cols:
            safe_cell = safe_html_text(r[c])
            html += f"<td>{safe_cell}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def generate_table1(df: pd.DataFrame, show_school: bool, show_count: bool, month_text: str) -> str:
    df_active = df[df[COL_STATUS] == "재원"].copy()
    safe_month_text = safe_html_text(month_text)
    html = f"<h2 style='text-align:center; font-size:16pt;'>학년별 명단 ({safe_month_text})</h2>"

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
            names_final_str = " ".join([safe_html_text(x) for x in group_sorted[COL_NAME].tolist()])

        html += f"<tr><th>{grade}</th><td class='t1-names'>{names_final_str}</td><td>{len(group)}</td></tr>"
        total += len(group)

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
                groups.append(" ".join([safe_html_text(x) for x in school_group[COL_NAME].tolist()]))
            body = " ".join(groups)

        return f"<div class='t1-summary-line'><strong>{label}:</strong> {body}</div>"

    str_1day = get_summary_str(1, "주 1회", show_school, show_count)
    str_3day = get_summary_str(3, "주 3회", show_school, show_count)

    if str_1day:
        summary_texts.append(str_1day)
    if str_3day:
        summary_texts.append(str_3day)

    summary_final_str = "".join(summary_texts)

    html += f"<tr><th>합계</th><td class='t1-names t1-summary'>{summary_final_str}</td><td>{total}</td></tr></tbody></table>"
    return html


def generate_table2(
    df: pd.DataFrame,
    month_text: str,
    period_notes: dict[int, str] | None = None,
    show_period_notes: bool = True,
) -> str:
    if period_notes is None:
        period_notes = {}

    safe_month_text = safe_html_text(month_text)

    df_active = df[df[COL_STATUS] == "재원"].copy()
    html = f"<h2 class='no-print' style='text-align:center; font-size:16pt;'>{safe_month_text} 반편성 내역</h2>"
    target_days = ["월", "화", "수", "목"]

    periods_set = set()
    for p_str in df_active[COL_PERIOD]:
        for n in extract_period_numbers(p_str):
            if n > 0:
                periods_set.add(n)
    periods = sorted(periods_set) if periods_set else [1, 2, 3]

    for p in periods:
        html += "<div class='a4-print-box'><table class='weekly-table'><thead><tr>"
        html += "<th style='width:8%;'>수업시간</th>"
        for d in target_days:
            html += f"<th style='width:18.4%;'>{d}</th>"
        html += "<th style='width:18.4%;'>비고</th></tr></thead><tbody>"

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
                students["_grade_order"] = (
                    students[COL_GRADE].astype(str).str.strip().map(GRADE_SORT_MAP).fillna(999)
                )
                students = students.sort_values(["_grade_order", COL_SCHOOL, COL_NAME])

                for _, r in students.iterrows():
                    grade = str(r[COL_GRADE]).strip()

                    if last_grade is not None and grade != last_grade:
                        student_list.append("<div style='height: 8px;'></div>")

                    s_str, g_str = str(r[COL_SCHOOL]).strip(), grade
                    school_grade = s_str + (g_str[1:] if s_str and g_str and s_str[-1] == g_str[0] else g_str)

                    raw_name = str(r[COL_NAME]).strip()
                    safe_name = safe_html_text(raw_name)
                    safe_school_grade = safe_html_text(school_grade)

                    raw_memo = str(r.get(COL_STUDENT_MEMO, "")).strip()
                    safe_memo = safe_html_text(raw_memo)

                    if raw_memo and len(raw_memo) >= 6:
                        student_html = (
                            "<div class='weekly-name-wrap weekly-name-wrap-vertical' style='text-align:left;'>"
                            f"<span class='weekly-name-text'>{safe_name} ({safe_school_grade})</span>"
                            f"<span class='weekly-name-memo weekly-name-memo-below'>{safe_memo}</span>"
                            "</div>"
                        )
                    elif raw_memo:
                        student_html = (
                            "<div class='weekly-name weekly-name-wrap' style='text-align:left;'>"
                            f"<span class='weekly-name-text'>{safe_name} ({safe_school_grade})</span>"
                            f"<span class='weekly-name-memo'>{safe_memo}</span>"
                            "</div>"
                        )
                    else:
                        student_html = (
                            f"<div class='weekly-name' style='text-align:left;'>{safe_name} ({safe_school_grade})</div>"
                        )

                    student_list.append(student_html)
                    last_grade = grade

            count_html = (
                f"<div class='weekly-name weekly-count' style='text-align:left; font-weight:bold; margin-top:4px;'>{len(students)}명</div>"
                if len(students) > 0 else ""
            )

            html += (
                f"<td style='text-align:left !important;'>"
                f"{''.join(student_list)}{count_html}</td>"
            )

        raw_period_note = str(period_notes.get(p, "")).strip() if show_period_notes else ""
        safe_period_note = safe_html_text(raw_period_note)

        note_html = (
            f"<div class='weekly-note-cell'>{safe_period_note}</div>"
            if safe_period_note else ""
        )

        html += f"<td style='text-align:left !important;'>{note_html}</td>"
        html += f"</tr></tbody></table><div class='date-footer'>{safe_month_text}</div></div>"

    return html


def generate_table3(
    df: pd.DataFrame,
    target_date,
    include_paused: bool,
    assignment_map: dict,
    teacher_notes: dict[int, str] | None = None,
) -> str:
    if teacher_notes is None:
        teacher_notes = {1: "", 2: "", 3: ""}

    weekday = WEEKDAY_ORDER[target_date.weekday()]
    day_mask = df[COL_DAYS].astype(str).apply(lambda x: weekday in split_days(x))
    df_day = df[day_mask].copy()

    if not include_paused:
        df_day = df_day[df_day[COL_STATUS] == "재원"]

    html = (
        f"<h2 class='t3-title' style='text-align:left; font-size:16pt; border-bottom:2px solid black;"
        f" padding-bottom:5px; margin:0 0 8px 0;'>"
        f"{target_date.month}-{target_date.day} {weekday}</h2>"
    )
    html += "<div class='daily-grid-container'>"

    rows = {1: [], 2: [], 3: []}

    for p in [1, 2, 3]:
        df_p = filter_students_for_day_period(df_day, weekday, p)
        if df_p.empty:
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

        for _, row in df_p.iterrows():
            grade = str(row[COL_GRADE]).replace("\u00A0", "").replace("\u3000", "").strip()
            is_new_grade = (last_grade is not None and grade != last_grade)

            pause = " (휴)" if row[COL_STATUS] == "휴원" else ""
            s_str = str(row[COL_SCHOOL]).strip()
            school_grade = s_str + (grade[1:] if s_str and grade and s_str[-1] == grade[0] else grade)

            raw_name_text = f"{row[COL_NAME]} ({school_grade}){pause}"
            safe_name_text = safe_html_text(raw_name_text)

            skey = get_student_key(row)
            akey = (p, skey)

            data = assignment_map.get(akey, {"letter": "", "absent": False})
            if not isinstance(data, dict):
                data = {"letter": sanitize_letter(str(data)), "absent": False}

            letter = sanitize_letter(data.get("letter", ""))
            is_abs = bool(data.get("absent", False))

            raw_memo = str(row.get(COL_STUDENT_MEMO, "")).strip()
            safe_memo = safe_html_text(raw_memo)

            if is_abs:
                p_absent += 1
            else:
                p_count += 1
                if letter:
                    p_alpha_counts[letter] = p_alpha_counts.get(letter, 0) + 1

            rows[p].append({
                "type": "student",
                "name_text": safe_name_text,
                "letter": letter,
                "memo": safe_memo,
                "raw_memo_len": len(raw_memo),
                "is_abs": is_abs,
                "is_new_grade": is_new_grade,
            })

            last_grade = grade

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
                rows[p].append({"type": "gap"})
                for i, line_text in enumerate(summary_lines):
                    rows[p].append({
                        "type": "summary",
                        "text": line_text,
                        "show_teacher_note": (i == 0),
                        "teacher_note": teacher_notes.get(p, ""),
                    })

    max_len = max(len(rows[1]), len(rows[2]), len(rows[3])) if not df_day.empty else 0

    for p in [1, 2, 3]:
        while len(rows[p]) < max_len:
            rows[p].append({"type": "blank"})
        rows[p].append({"type": "bottom"})

    th_name = "66%"
    th_small = "11.33%"

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
                memo = item.get("memo", "")
                memo_len = item.get("raw_memo_len", 0)

                if memo and memo_len >= 7:
                    name_html = (
                        f"<div class='student-inner{gap_class} t3-name-wrap t3-name-wrap-vertical'>"
                        f"    <span class='t3-name-text'>{name_text}</span>"
                        f"    <span class='t3-name-memo t3-name-memo-below'>{memo}</span>"
                        f"</div>"
                    )
                else:
                    name_html = (
                        f"<div class='student-inner{gap_class} t3-name-wrap'>"
                        f"    <span class='t3-name-text'>{name_text}</span>"
                        f"    <span class='t3-name-memo'>{memo}</span>"
                        f"</div>"
                    )

                html += (
                    "<tr class='t3-row'>"
                    f"<td class='name-cell{abs_class}'>"
                    f"{name_html}"
                    f"</td>"
                    f"<td><div class='student-inner{gap_class}'><div class='check-box'></div></div></td>"
                    f"<td><div class='student-inner{gap_class}'>&nbsp;</div></td>"
                    f"<td class='assign-cell'><div class='student-inner{gap_class}'>{letter}</div></td>"
                    "</tr>"
                )

            elif t == "summary":
                text = item.get("text", "")
                show_teacher_note = item.get("show_teacher_note", False)
                raw_teacher_note = str(item.get("teacher_note", "")).strip()
                safe_teacher_note = safe_html_text(raw_teacher_note)

                if show_teacher_note and safe_teacher_note:
                    html += (
                        "<tr class='t3-row'>"
                        "<td class='summary-cell'>"
                        "  <div class='t3-summary-wrap'>"
                        f"      <div class='t3-summary-text'>{text}</div>"
                        f"      <div class='t3-summary-memo'>{safe_teacher_note}</div>"
                        "  </div>"
                        "</td>"
                        "<td></td><td></td><td></td>"
                        "</tr>"
                    )
                else:
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

    html += "</div>"
    return html


def generate_table4(df: pd.DataFrame, show_grade: bool, month_text: str) -> str:
    df_active = df[df[COL_STATUS] == "재원"].copy()

    unique_schools = df_active[COL_SCHOOL].dropna().unique().tolist()
    unique_schools.sort(key=lambda x: (get_school_rank(x), str(x)))

    safe_month_text = safe_html_text(month_text)
    html = f"<h2 style='text-align:center; font-size:16pt;'>학교별 명단 ({safe_month_text})</h2>"

    html += "<table class='table1-custom table4-custom'><thead><tr><th>학교</th><th>학생 명단</th><th>인원수</th></tr></thead><tbody>"

    total = 0
    for school in unique_schools:
        group = df_active[df_active[COL_SCHOOL] == school].copy()
        if group.empty:
            continue

        group["_grade_clean"] = group[COL_GRADE].astype(str).str.strip()
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
            names_final_str = " ".join([safe_html_text(x) for x in group_sorted[COL_NAME].tolist()])

        safe_school = safe_html_text(school)
        html += f"<tr><th>{safe_school}</th><td class='t1-names'>{names_final_str}</td><td>{len(group)}</td></tr>"
        total += len(group)

    html += f"<tr><th>합계</th><td class='t1-names'></td><td>{total}</td></tr></tbody></table>"

    return html