
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Optimización de Listado", layout="wide")
st.title("Optimización de Listado - Dashboard")

archivo = st.file_uploader("📤 Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    try:
        df_asin = pd.read_excel(archivo, sheet_name="CustListing")
        df_kw = pd.read_excel(archivo, sheet_name="CustKW")
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    pestaña = st.radio("Selecciona una sección:", ["🧾 Listado de ASINs", "🔍 Palabras Clave (Keywords)"])

    if pestaña == "🧾 Listado de ASINs":
        st.subheader("Listado de productos por ASIN")
        for _, row in df_asin.iterrows():
            asin = row.get("ASIN", "")
            titulo = row.get("Product Title", "")
            bullets = row.get("Bullet Points", "")
            descripcion = row.get("Description", "")

            with st.expander(f"ASIN: {asin}"):
                st.markdown("**Título del producto:**")
                st.write(titulo)
                st.markdown("---")
                st.markdown("**Puntos clave:**")
                st.write(bullets)
                if pd.notna(descripcion) and str(descripcion).strip():
                    st.markdown("---")
                    st.markdown("**Descripción:**")
                    st.write(descripcion)

    elif pestaña == "🔍 Palabras Clave (Keywords)":
        st.subheader("Palabras clave del producto")
        opciones = {
            "Mayor al 5%": 0.05,
            "Mayor al 2.5%": 0.025
        }
        seleccion = st.selectbox("Filtrar por porcentaje de clics (Click Share):", list(opciones.keys()))
        umbral = opciones[seleccion]

        # Ya están como decimales reales
        df_kw["Click Share"] = pd.to_numeric(df_kw["Click Share"], errors="coerce")
        filtrado = df_kw[df_kw["Click Share"] > umbral]

        columnas_a_mostrar = {
            "Keyword": "Palabra clave",
            "Estimated Weekly Impressions": "Impresiones mensuales",
            "Click Share": "Porcentaje de clics"
        }

        st.dataframe(filtrado[list(columnas_a_mostrar.keys())].rename(columns=columnas_a_mostrar))
