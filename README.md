# Academy Student & Attendance Management System
반복적인 학원 문서 관리 업무를 자동화하기 위해 개발한 Streamlit 기반 웹 애플리케이션입니다.
학생 데이터를 단일 원장에서 관리하고,
학생 명단, 반편성표, 일일 출석부, 학교별 명단을 자동 생성하며
출석 및 배정 정보를 저장·복원할 수 있습니다.

⚠️ 본 저장소는 가상 학생 데이터를 활용한 공개 데모 버전입니다.

Demo: <https://academy-app-shown-j5s336qqguyun3igzkfdkr.streamlit.app/>

## 1. 프로젝트 배경
## Problem
학원 운영자는 학생 정보가 변경될 때마다
```
- 학생 명단
- 반편성표
- 일일 출석부
- 학교별 명단
```
을 각각 수정해야 했습니다.
학생 한 명의 요일이나 교시가 변경되면 여러 문서를 반복 수정해야 했고,
문서 간 불일치와 인쇄 준비 작업이 빈번하게 발생했습니다.

## Solution
Google Sheets를 단일 데이터 원장으로 사용하고,
Streamlit 웹 인터페이스를 통해 필요한 문서를 자동 생성하도록 구성했습니다.
학생 정보는 한 곳에서만 관리하고,
모든 출력물은 해당 데이터를 기준으로 자동 생성됩니다.

## 2. 시스템 구조
```
Google Sheets
      │
      ▼
 Streamlit
      │
      ├─ 학생 명단
      ├─ 반편성표
      ├─ 출석부
      └─ 학교별 명단
```

## 3. 주요 기능
① 전체 학생 목록
<img width="854" height="292" alt="화면 캡처 2026-06-02 083905" src="https://github.com/user-attachments/assets/8d3168bd-3e5a-469e-8ae7-065947ff10cf" />

Google Sheets에 저장된 학생 정보를 실시간으로 조회할 수 있습니다.
이름, 학교, 학년, 등원요일, 수업교시, 상태 정보를 한 화면에서 확인할 수 있으며,
검색 기능을 통해 특정 학생을 빠르게 찾을 수 있고,
전체 목록을 인쇄하거나 검색 결과에 나온 학생들만 포함해 인쇄할 수 있습니다

② 학년별 명단
<img width="895" height="405" alt="화면 캡처 2026-06-02 084809" src="https://github.com/user-attachments/assets/cef4f4dc-0c41-40f2-8079-ed8511bd6c20" />
학생 데이터를 학년 기준으로 자동 정렬하여 출력합니다.
학교명 표시 여부와 학교별 인원수 표시 여부를 선택할 수 있으며,
인쇄용 명단 생성에 최적화되어 있습니다.

③ 반편성표
<img width="857" height="401" alt="화면 캡처 2026-06-02 085012" src="https://github.com/user-attachments/assets/580c89de-2c04-4c2f-bdc5-435d3b64c133" />
학생의 등원요일과 수업교시 정보를 기반으로
요일·교시별 반편성표를 자동 생성합니다.
학생 정보가 변경되면 별도 수정 없이
최신 반편성표가 즉시 반영됩니다.
현재 명단과 다음달 명단을 분리하여 관리할 수 있습니다.

④ 일일 출석부

[웹 입력 화면]
<img width="866" height="402" alt="화면 캡처 2026-06-02 085330" src="https://github.com/user-attachments/assets/d5bebae1-5c21-4184-96e2-4c2555fe0671" />
[인쇄 결과물]
<img width="2479" height="3508" alt="학생 인원관리 시스템 (Demo) · Streamlit_1" src="https://github.com/user-attachments/assets/da3c4fc9-6f0b-4394-ae69-6a009f2bb5f0" />

선택한 날짜의 학생 명단을 자동 생성하고,
배정 알파벳 입력, 결석 처리, 교시별 메모 작성 기능을 제공합니다.
학생별 메모는 반편성표에 입력된 내용을 공유하게 하여, 인원을 더 수월하게 관리할 수 있도록 합니다.
입력된 데이터는 날짜 기준으로 저장되며,
새로고침 또는 재접속 이후에도 복원됩니다.
저장된 정보를 기반으로 인쇄용 출석부를 생성할 수 있습니다.

⑤ 학교별 명단
<img width="854" height="368" alt="화면 캡처 2026-06-02 085647" src="https://github.com/user-attachments/assets/121ff7d0-f6bb-4bb3-95c2-6d81eba83f26" />
학생을 학교 기준으로 그룹화하여 출력합니다.
학교별 학생 수를 확인할 수 있으며,
학교 방문 상담, 홍보, 행정 업무에 활용할 수 있습니다.

## 4. 부가 기능
-출석 데이터 저장 및 복원

배정 정보, 결석 여부, 교시별 메모를 Google Sheets에 저장합니다.
저장된 데이터는 날짜 기준으로 불러올 수 있으며,
사용자가 다시 접속하더라도 이전 상태를 복원할 수 있습니다.

-인쇄 최적화

A4 출력 환경에 맞춰 레이아웃을 최적화했습니다.
화면 입력 요소는 인쇄 시 자동 제외되며,
세로/가로 방향 선택과 출력물 가독성을 고려한 스타일을 제공합니다.

## 5. Demo GIF
<img width="1916" height="646" alt="091839" src="https://github.com/user-attachments/assets/5eb83a41-31a2-4e0a-86ac-1ea01ac0b82d" />

## 6. 기술 스택
```
### Frontend
- Streamlit
### Data Processing
- Pandas
### Data Storage
- Google Sheets
- gspread
- Google Sheets API
### Automation
- Google Apps Script
### Deployment
- Streamlit Community Cloud
```

## 6. 프로젝트 구조
```
academy/
 ├ config.py
 ├ data.py
 ├ filters.py
 ├ tables.py
 ├ styles.py
 ├ backup.py
 ├ utils.py
 └ ui.py
app.py
```
## 7. 개선 과정
⸻

1. 학생ID 관리

동일 학생이 현재월/다음달 명단에서
다른 학생으로 인식되는 문제 해결
학생ID 기준 관리 체계 도입

⸻

2. 출석 데이터 저장 구조

배정 정보
결석 정보
교시별 메모
날짜 기준 저장 및 복원 기능 구현

⸻

3. 인쇄 UX 개선

A4 출력 최적화
열 너비 조정
입력 UI 자동 숨김

⸻

4. 데이터 정규화

KeyError: '학년'
컬럼명 정규화
필수 컬럼 검증 로직 추가

⸻

5. 학생ID 관리 자동화
현재월 명단(students)과 다음달 명단(students_next) 간
학생ID 불일치로 인해 동일 학생이 신규 학생으로 인식되는 문제가 발생했습니다.
이를 해결하기 위해 Google Apps Script를 활용하여:
- 학생ID 자동 생성
- students_next 학생ID 동기화
- 중복 및 누락 ID 검사

기능을 구현했습니다.
이를 통해 명단 비교 정확도를 높이고
사용자 입력 실수를 줄일 수 있었습니다.

⸻
## 8. 향후 개선 사항
- 사용자 인증
- 권한 관리
- 월별 통계
- 더 많은 인원 관리
- 문서 양식 커스터마이징 기능 제공

⸻

Author

Developed by Minji Kim, as a project to automate repetitive document generation in academy administration.
