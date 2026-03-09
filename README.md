# Academy Document Generation system
**[Details]**

A web application that automatically generates academy management documents
such as student lists, class schedules, and attendance sheets using Google Sheets data.

This tool was developed to replace repetitive manual document creation
in a real academy environment.

**[Features]**

- Google Sheets based student data integration
- Automatic generation of student lists by grade and school
- Class assignment tables by day and period
- Interactive attendance assignment editor
- A4 optimized printing layout

**[Tech stack]**

Python
Streamlit
Pandas
Google Sheets API (gspread)
HTML / CSS

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
