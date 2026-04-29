# academy/styles.py
import streamlit as st


def get_print_css(orientation: str = "세로") -> str:
    page_size = "A4 portrait" if orientation == "세로" else "A4 landscape"

    # 인쇄 페이지 여백
    page_margin_top = "3mm"
    page_margin_lr = "5mm"
    note_height = "950px" if orientation == "세로" else "660px"

    # 2번표: 한 줄형 메모만 가로/세로 분기
    if orientation == "세로":
        weekly_name_inline_css = """
        .weekly-name-wrap {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 2px;
            width: 100%;
        }

        .weekly-name-text {
            flex: 1 1 auto;
            min-width: 0;
            overflow: hidden;
        }

        .weekly-name-memo {
            flex: 0 0 auto;
            width: 56px;
            min-width: 56px;
            font-size: 7pt;
            line-height: 1.15;
            color: #2563eb;
            text-align: right;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: clip;
            padding-right: 3px;
            box-sizing: border-box;
        }
        """
    else:
        weekly_name_inline_css = """
        .weekly-name-wrap {
            display: flex;
            justify-content: flex-start;
            align-items: baseline;
            gap: 8px;
            width: 100%;
        }

        .weekly-name-text {
            flex: 0 1 auto;
            min-width: 0;
            overflow: hidden;
        }

        .weekly-name-memo {
            flex: 0 0 auto;
            width: auto;
            min-width: 0;
            font-size: 7pt;
            line-height: 1.15;
            color: #2563eb;
            text-align: left;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: clip;
            padding-right: 0;
            box-sizing: border-box;
        }
        """

    return f"""
    <style>
        /* =========================================================
           @page (인쇄 페이지 설정)
           ========================================================= */
        @page {{
            size: {page_size};
            margin: {page_margin_top} {page_margin_lr};
        }}

        /* =========================================================
           공통 (화면 + 인쇄)
           ========================================================= */
        html, body, .stApp {{
            font-family:
              "Malgun Gothic",
              "맑은 고딕",
              "Apple SD Gothic Neo",
              "Noto Sans KR",
              sans-serif !important;
        }}

        div[data-testid="stTextArea"] textarea {{
            font-size: 14px !important;
            line-height: 1.4 !important;
        }}

        /* =========================================================
           Selectbox 커서
           ========================================================= */
        div[data-baseweb="select"] * {{
            cursor: pointer !important;
        }}

        div[role="listbox"] *,
        li[role="option"] * {{
            cursor: pointer !important;
        }}

        .report-view {{
            border: 1px solid #ccc;
            padding: 20px;
            background: white;
            margin-top: 20px;
            color: black;
        }}

        .a4-print-box {{
            margin-bottom: 15px;
            page-break-after: always;
            break-after: page;
        }}

        .a4-print-box:last-child {{
            page-break-after: auto;
            break-after: auto;
        }}

        .date-footer {{
            margin-top: 5px;
            text-align: right;
            font-size: 11pt;
            color: #666;
        }}

        /* 화면용 빈 네모 (결석/숙제 수기 체크용) */
        .check-box {{
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 1px solid #000;
            vertical-align: middle;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
            margin-bottom: 10px;
        }}

        th {{
            border: 1px solid #ccc !important;
            padding: 8px 4px !important;
            text-align: center !important;
            vertical-align: middle !important;
            white-space: nowrap !important;
            word-break: keep-all !important;
            font-size: 10pt !important;
            background-color: #F1F5F9 !important;
            color: black !important;
            font-weight: 600;
        }}

        td {{
            border: 1px solid #ccc;
            padding: 6px 4px;
            text-align: center;
            vertical-align: middle !important;
            word-wrap: break-word;
            font-size: 10pt;
            color: black;
        }}

        /* =========================================================
           3번표(출석부) 화면용 이름 말줄임
           ========================================================= */
        .daily-table td.name-cell {{
            text-align: left;
            padding-left: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 10pt;
            letter-spacing: -0.2px;
        }}

        /* =========================================================
           1번표 / 4번표
           ========================================================= */
        .table1-custom {{
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }}

        .table1-custom th:first-child,
        .table1-custom td:first-child {{
            width: 8% !important;
        }}

        .table1-custom th:last-child,
        .table1-custom td:last-child {{
            width: 8% !important;
        }}

        .table1-custom th,
        .table1-custom td {{
            font-size: 11pt !important;
        }}

        .table1-custom .t1-names {{
            text-align: left !important;
            vertical-align: top !important;
            padding: 8px 6px !important;
            font-size: 10.5pt !important;
            line-height: 1.8 !important;
            word-break: keep-all !important;
        }}

        .table4-custom th:first-child,
        .table4-custom td:first-child {{
            width: 14% !important;
        }}

        /* =========================================================
           2번표(주간표)
           ========================================================= */
        .weekly-table td {{
            vertical-align: top !important;
            padding-top: 2px !important;
        }}

        .weekly-table td.period-cell {{
            vertical-align: middle !important;
            text-align: center !important;
            font-weight: bold !important;
        }}

        {weekly_name_inline_css}

        .weekly-name {{
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 8pt;
            letter-spacing: -0.6px;
            margin-bottom: 5px;
            line-height: 1;
        }}

        /* 긴 메모(아래형)는 공통 유지 */

        .weekly-name-wrap-vertical {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            justify-content: flex-start;
            gap: 0;
            width: 100%;
            overflow: visible !important;
        }}

        .weekly-name-wrap-vertical .weekly-name-text {{
            display: block;
            flex: none !important;
            min-width: auto !important;
            overflow: visible !important;
            white-space: nowrap;
            text-overflow: clip !important;
            font-size: 8pt;
            letter-spacing: -0.6px;
            line-height: 1.05;
        }}

        .weekly-name-memo-below {{
            display: block;
            width: auto;
            min-width: 0;
            max-width: 100%;
            font-size: 6.5pt;
            line-height: 1.0;
            color: #2563eb;
            text-align: left;
            white-space: nowrap;
            overflow: visible !important;
            padding-right: 0;
            box-sizing: border-box;
        }}

        .weekly-note-cell {{
            font-size: 8pt;
            line-height: 1.3;
            white-space: pre-wrap;
            word-break: keep-all;
            overflow-wrap: break-word;
            text-align: left;

            min-height: {note_height};
            max-height: {note_height};
            overflow: hidden;
            box-sizing: border-box;
        }}

        .weekly-count {{
            margin-top: 4px;
        }}

        /* =========================================================
           3번표(일일 출석부)
           ========================================================= */
        .daily-grid-container {{
            display: flex;
            width: 100%;
            gap: 6px;
            align-items: flex-start;
        }}

        .period-column {{
            flex: 1 1 0;
            min-width: 0;
        }}

        .period-column table {{
            width: 100%;
        }}

        .table3-custom {{
            border-collapse: collapse !important;
            width: 100%;
        }}

        .table3-custom,
        .table3-custom thead,
        .table3-custom tbody,
        .table3-custom tr {{
            border-top: 0 !important;
            border-bottom: 0 !important;
        }}

        .table3-custom th,
        .table3-custom td {{
            border: none !important;
            border-top: 0 !important;
            border-bottom: 0 !important;
            border-left: 1px solid #999 !important;
            border-right: 1px solid #999 !important;
        }}

        .table3-custom thead th {{
            border-top: 1px solid #000 !important;
            border-bottom: 2px solid #000 !important;
            writing-mode: horizontal-tb !important;
            transform: none !important;
            white-space: nowrap !important;
            word-break: keep-all !important;
            padding: 4px 2px !important;
            overflow: hidden !important;
            text-overflow: clip !important;
        }}

        .table3-custom th:first-child,
        .table3-custom td:first-child {{
            border-left: 1px solid #000 !important;
        }}

        .table3-custom th:last-child,
        .table3-custom td:last-child {{
            border-right: 1px solid #000 !important;
        }}

        .table3-custom .name-cell.absent {{
            text-decoration: line-through !important;
        }}

        .table3-custom .student-inner {{
            font-size: 10pt !important;
            line-height: 1.5;
        }}

        .table3-custom .student-inner.new-grade-gap {{
            padding-top: 7px !important;
        }}

        .table3-custom .summary-cell {{
            text-align: left !important;
            padding: 2px 4px !important;
            font-size: 10.5pt !important;
            line-height: 1.2 !important;
        }}

        .table3-custom td.t3-gap {{
            padding: 0 !important;
            height: 3px !important;
            line-height: 0 !important;
            font-size: 0 !important;
        }}

        .table3-custom .t3-name-wrap {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 8px;
            width: 100%;
        }}

        .table3-custom .t3-name-text {{
            flex: 1 1 auto;
            min-width: 0;
        }}

        .table3-custom .t3-name-memo {{
            flex: 0 0 auto;
            max-width: 72px;
            font-size: 7pt;
            color: #2563eb;
            text-align: left;
            white-space: nowrap;
            overflow: hidden;
        }}

        .table3-custom .t3-name-wrap-vertical {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            gap: 1px;
        }}

        .table3-custom .t3-name-memo-below {{
            display: block;
            max-width: none;
            font-size: 7pt;
            color: #2563eb;
            line-height: 1.1;
            text-align: left;
            white-space: nowrap;
            overflow: hidden;
        }}

        .table3-custom .t3-summary-wrap {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 8px;
            width: 100%;
        }}

        .table3-custom .t3-summary-text {{
            flex: 1 1 auto;
            min-width: 0;
        }}

        .table3-custom .t3-summary-memo {{
            flex: 0 0 84px;
            font-size: 9pt;
            line-height: 1.25;
            text-align: left;
            white-space: pre-wrap;
            word-break: keep-all;
            overflow-wrap: break-word;
            color: #000000;
        }}

        .table3-custom tbody tr.t3-bottom td {{
            padding: 0 !important;
            height: 0 !important;
            line-height: 0 !important;
            font-size: 0 !important;
            border-top: 1.5px solid #000 !important;
            border-bottom: none !important;
            border-left: none !important;
            border-right: none !important;
        }}

        .assign-cell {{
            font-weight: normal;
        }}

        /* =========================================================
           화면 전용
           ========================================================= */
        @media screen {{
            .print-only {{
                display: none !important;
            }}

            .tab0-print-root {{
                display: none !important;
            }}
        }}

        /* =========================================================
           인쇄 전용
           ========================================================= */
        @media print {{
            /* -----------------------------------------------------
            1) 기본: 전부 숨김
            ----------------------------------------------------- */
            body * {{
                visibility: hidden !important;
            }}
            /* -----------------------------------------------------
            2) 인쇄 대상만 표시
            ----------------------------------------------------- */
            .print-area,
            .print-area * {{
                visibility: visible !important;
            }}
            /* -----------------------------------------------------
            3) 인쇄 대상 위치 보정
            ----------------------------------------------------- */
            .print-area {{
                position: fixed !important;
                left: 0 !important;
                top: 0 !important;
                width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                z-index: 9999 !important;
            }}
            /* -----------------------------------------------------
            4) 페이지 여백 초기화
            ----------------------------------------------------- */
            html, body, .stApp, .stAppViewContainer,
            section.main, .main, .block-container {{
                margin: 0 !important;
                padding: 0 !important;
            }}
            .report-view {{
                margin: 0 !important;
                padding: 0 !important;
                border: none !important;
                background: #fff !important;
            }}
            .tab0-print-root {{
                display: block !important;
            }}
            /* -----------------------------------------------------
            5) 기본 테이블 인쇄 스타일
            ----------------------------------------------------- */
            table {{
                font-size: 7.5pt !important;
                border: 1px solid #000 !important;
                margin-bottom: 5px !important;
                page-break-inside: auto;
            }}
            tr {{
                page-break-inside: avoid;
                page-break-after: auto;
            }}
            table:not(.table3-custom) th,
            table:not(.table3-custom) td {{
                border: 1px solid #000 !important;
                color: #000 !important;
            }}
            /* -----------------------------------------------------
            6) 0번표(전체 목록) 인쇄 전용
            ----------------------------------------------------- */
            .tab0-print-root table.total-list-table,
            .tab0-print-root table.total-list-table th,
            .tab0-print-root table.total-list-table td {{
                border: 1px solid #A2A2A2 !important;
            }}
            table.total-list-table thead {{
                display: table-header-group !important;
            }}
            table.total-list-table tr {{
                page-break-inside: auto !important;
                break-inside: auto !important;
            }}
            table.total-list-table tbody {{
                break-inside: auto !important;
            }}
            .tab0-print-header {{
                display: flex !important;
                justify-content: space-between !important;
                align-items: flex-end !important;
                margin: 0 0 10px 0 !important;
                padding-top: 2mm !important;
            }}
            .tab0-print-title {{
                text-align: left !important;
                font-size: 16pt !important;
                margin: 0 !important;
                padding: 0 !important;
            }}
            .tab0-print-count {{
                font-size: 11pt !important;
                color: #000 !important;
                font-weight: 700 !important;
                margin-left: 6px !important;
            }}
            .tab0-print-search-msg {{
                font-size: 11pt !important;
                color: #000 !important;
                font-weight: 500 !important;
                margin-bottom: 2px !important;
            }}
            /* -----------------------------------------------------
            7) 2번표(주간표) 인쇄 보정
            ----------------------------------------------------- */
            .weekly-table {{
                width: 100% !important;
                max-width: 100% !important;
                margin-left: 0 !important;
                box-sizing: border-box !important;
                table-layout: fixed !important;
            }}
            .weekly-note-header {{
                display: none !important;
            }}
            /* -----------------------------------------------------
            8) 3번표(출석부) 인쇄 전용 스타일
            ----------------------------------------------------- */
            .table3-custom th,
            .table3-custom td {{
                border-left: 1px solid #000 !important;
                border-right: 1px solid #000 !important;
            }}
            .table3-custom thead th {{
                border-top: 1px solid #000 !important;
                border-bottom: 2px solid #000 !important;
                writing-mode: horizontal-tb !important;
                transform: none !important;
                white-space: nowrap !important;
                letter-spacing: -0.5px !important;
            }}
            .table3-custom th:first-child,
            .table3-custom td:first-child {{
                border-left: 2px solid #000 !important;
            }}
            .table3-custom th:last-child,
            .table3-custom td:last-child {{
                border-right: 2px solid #000 !important;
            }}
            .table3-custom tbody tr.t3-bottom td {{
                padding: 0 !important;
                height: 0 !important;
                line-height: 0 !important;
                font-size: 0 !important;
                border-top: 2px solid #000 !important;
                border-bottom: none !important;
                border-left: none !important;
                border-right: none !important;
                background: transparent !important;
            }}
            .table3-custom .student-inner {{
                font-size: 9.5pt !important;
            }}
            .table3-custom .summary-cell {{
                font-size: 8.5pt !important;
                line-height: 0.8 !important;
                padding: 2px 4px !important;
                vertical-align: top !important;
            }}
            .table3-custom td.t3-gap {{
                height: 3px !important;
                padding: 0 !important;
                line-height: 0 !important;
                font-size: 0 !important;
            }}
            /* -----------------------------------------------------
            9) 인쇄 가독성 공통 보정
            ----------------------------------------------------- */
            th {{
                background-color: #F1F5F9 !important;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
                font-size: 8pt !important;
                padding: 4px 2px !important;
                letter-spacing: -0.5px !important;
            }}
            td {{
                padding: 2px 1px !important;
                line-height: 1.0 !important;
            }}
            .daily-grid-container {{
                gap: 4px !important;
            }}
            .check-box {{
                width: 14px !important;
                height: 14px !important;
                border: 2px solid black !important;
            }}
            /* -----------------------------------------------------
            10) 1번표 / 페이지 에어백
            ----------------------------------------------------- */
            .table1-custom th,
            .table1-custom td:not(.t1-names) {{
                font-size: 10pt !important;
            }}
            .table1-custom .t1-names {{
                font-size: 10.5pt !important;
                padding: 8px 6px !important;
                line-height: 1.65 !important;
            }}
            .a4-print-box {{
                padding-top: 2mm !important;
            }}
            .a4-print-box + .a4-print-box {{
                padding-top: 6mm !important;
            }}
        }}    </style>
    """

@st.cache_data
def get_print_css_cached(orientation: str) -> str:
    return get_print_css(orientation)