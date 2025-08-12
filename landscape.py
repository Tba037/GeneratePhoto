import streamlit as st
import pandas as pd
from io import BytesIO

#SetupPage
byfile = st.Page(
     page="Project2.py",
     title="Versi 2",
     icon="📁",
)
bylist = st.Page(
     page="Project1.py",
     title="Versi 1",
     icon="📃",
     default=True,
)

pg = st.navigation({"Choose": [bylist, byfile],})

pg.run()