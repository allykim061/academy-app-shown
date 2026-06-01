# app.py
import streamlit as st

from academy.config import PAGE_TITLE
from academy.ui import run_app


def main():
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon="📚",
        layout="wide",
    )
    run_app()


if __name__ == "__main__":
    main()