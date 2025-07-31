
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

    with st.expander("📦 Datos del cliente", expanded=True):
        subtabs = st.radio("Selecciona una vista:", ["🧾 Listado de ASINs", "🔍 Palabras Clave (Keywords)"])

        if subtabs == "🧾 Listado de ASINs":
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

        elif subtabs == "🔍 Palabras Clave (Keywords)":
            st.subheader("Palabras clave del producto")
            opciones = {
                "Mayor al 5%": 0.05,
                "Mayor al 2.5%": 0.025
            }
            seleccion = st.selectbox("Filtrar por porcentaje de clics (Click Share):", list(opciones.keys()))
            umbral = opciones[seleccion]

            df_kw["Click Share"] = pd.to_numeric(df_kw["Click Share"], errors="coerce")
            df_kw_filtrado = df_kw[df_kw["Click Share"].fillna(0) > umbral].copy()

            df_kw_filtrado["Click Share"] = (df_kw_filtrado["Click Share"] * 100).round(2).astype(str) + "%"
            df_kw_filtrado["M. Searches"] = pd.to_numeric(df_kw_filtrado["M. Searches"], errors="coerce").fillna(0).astype(int)

            columnas_a_mostrar = {
                "Keyword": "Palabra clave",
                "M. Searches": "Impresiones mensuales",
                "Click Share": "Porcentaje de clics"
            }

            df_visual = df_kw_filtrado[list(columnas_a_mostrar.keys())].rename(columns=columnas_a_mostrar)

            st.dataframe(df_visual.style.set_properties(**{
                "white-space": "nowrap",
                "text-overflow": "ellipsis",
                "overflow": "hidden",
                "max-width": "300px"
            }))
