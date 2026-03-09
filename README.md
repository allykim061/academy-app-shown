# Academy Document Generation system

**[Details]**

학원 운영에서 반복적으로 생성되는 문서 작업을 자동화하기 위해 개발된 웹 애플리케이션입니다.
Google Sheets에 저장된 학생 데이터를 기반으로 다음과 같은 문서를 자동으로 생성합니다:
	•	학생 전체 명단
	•	학년별 명단
	•	수업시간별 명단
	•	일일 출석부
	•	학교별 명단

Streamlit 기반 웹 인터페이스를 통해 데이터를 불러오고, A4 인쇄에 최적화된 문서를 생성할 수 있습니다.
 
A Streamlit-based web application that automatically generates academy management documents such as student lists, class schedules, and attendance sheets using Google Sheets data.

This project was developed to replace repetitive manual document creation in a real academy environment.

⸻

**[Problems]**

In many academies, documents such as student lists, class schedules, and attendance sheets are created manually from spreadsheet data.

This process often involves:
	•	Repeated copying and formatting
	•	Manual sorting of students by grade or school
	•	Creating printable documents for daily operations

These repetitive tasks are time-consuming and prone to formatting inconsistencies.

⸻

**[Solution]**

This application converts structured student data stored in Google Sheets into automatically generated documents through a web interface.

The system allows users to:
	•	Load student data from Google Sheets
	•	Automatically generate multiple document formats
	•	Manage attendance and class assignments
	•	Print A4-optimized documents for academy operations

 ⸻

**[Features]**

Student Data Integration
	•	Load student data directly from Google Sheets
	•	Manage school, grade, attendance days, and class periods

Automatic Document Generation

The system generates several types of academy documents:

1️⃣ Full Student List
Searchable roster of all registered students

<img width="854" height="377" alt="화면 캡처 2026-03-09 175905" src="https://github.com/user-attachments/assets/4d27ee0a-0ba7-48f7-9efa-eaefd8b42258" />

2️⃣ Grade-based Student List
Students grouped by grade with optional school grouping

<img width="545" height="355" alt="화면 캡처 2026-03-09 181230" src="https://github.com/user-attachments/assets/fd4828b8-aa62-452d-8a3a-f98a820392fb" />

3️⃣ Weekly Class Table
Students organized by weekday and class period

<img width="293" height="365" alt="화면 캡처 2026-03-09 181504" src="https://github.com/user-attachments/assets/65f11c9a-176f-4419-86d2-e3b2b0588185" />

4️⃣ Daily Attendance Sheet
Interactive attendance and assignment editor

5️⃣ School-based Student List
Students grouped by school

⸻

**[Tech stack]**

Python
Streamlit
Pandas
Google Sheets API (gspread)
HTML / CSS

⸻

**[Project Structure]**

```
academy/
 ├ config.py
 ├ data.py
 ├ filters.py
 ├ tables.py
 ├ styles.py
 └ ui.py

app.py
```
⸻

Version

v1.0

First stable release after codebase refactoring and structural cleanup.

⸻

Future Improvements
	•	User authentication and role management
	•	Attendance history storage
	•	Document customization options
	•	Performance optimization for larger student datasets

⸻

Author

Developed by Minji Kim, as a project to automate repetitive document generation in academy administration.
