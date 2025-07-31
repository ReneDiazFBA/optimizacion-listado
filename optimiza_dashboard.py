
import streamlit as st
import pandas as pd

st.title("Optimización de Listado - Dashboard")

uploaded_file = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name="CustListing")

    st.subheader("Listado de ASINs")

    for index, row in df.iterrows():
        asin = row.get("ASIN", "")
        title = row.get("Product Title", "")
        bullets = row.get("Bullet Points", "")
        description = row.get("Description", "")

        with st.expander(f"ASIN: {asin}"):
            st.markdown(f"**Título del producto:**\n\n{title}")
            st.markdown("---")
            st.markdown(f"**Bullet Points:**\n\n{bullets}")
            if pd.notna(description) and str(description).strip():
                st.markdown("---")
                st.markdown(f"**Descripción:**\n\n{description}")
