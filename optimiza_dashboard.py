
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Optimización de Listado", layout="wide")
st.title("Optimización de Listado - Dashboard")

archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    try:
        df_asin = pd.read_excel(archivo, sheet_name="CustListing")
        df_kw = pd.read_excel(archivo, sheet_name="CustKW")
        df_comp = pd.read_excel(archivo, sheet_name="CompKW", header=None)
        df_comp_data = pd.read_excel(archivo, sheet_name="CompKW", skiprows=2)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.stop()

    # --- DATOS DEL CLIENTE ---
    with st.expander("Datos del cliente", expanded=True):
        subtabs = st.radio("Selecciona una vista:", ["Listado de ASINs", "Palabras Clave (Keywords)"])

        if subtabs == "Listado de ASINs":
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

        elif subtabs == "Palabras Clave (Keywords)":
            st.subheader("Palabras clave del producto")
            opciones = {
                "Mayor al 5%": 0.05,
                "Mayor al 2.5%": 0.025
            }
            seleccion = st.selectbox("Filtrar por porcentaje de clics:", list(opciones.keys()))
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

    # --- DATOS DE COMPETIDORES ---
    with st.expander("Datos de competidores", expanded=True):
        st.subheader("ASIN de competidores")
        asin_raw = str(df_comp.iloc[0, 0])
        if "ExpandKeywords" in asin_raw:
            cuerpo = asin_raw.replace("ExpandKeywords(439)-US-", "").split("-Last-30-days")[0]
            asin_list = [a.strip() for a in cuerpo.split(",") if a.strip()]
            df_asin_comp = pd.DataFrame({"ASIN de competidor": asin_list})
            st.dataframe(df_asin_comp)
        else:
            st.warning("No se encontraron ASINs válidos en la celda [0, 0] de la hoja 'CompKW'.")

        st.subheader("Keywords por ranking de competidor")
        rango = st.selectbox("Mostrar keywords con ranking mayor a:", [4, 5, 6], index=1)

        # Limpiar espacios vacíos
        df_comp_data.replace(r'^\s*$', pd.NA, regex=True, inplace=True)

        # Seleccionar columnas y convertir datos
        cols = df_comp_data.iloc[:, [0, 5, 8, 18]].copy()
        cols.columns = ["Palabra clave", "Ranking ASIN", "Impresiones", "CTR"]

        cols["Ranking ASIN"] = pd.to_numeric(cols["Ranking ASIN"], errors="coerce")
        cols["Impresiones"] = pd.to_numeric(cols["Impresiones"], errors="coerce")
        cols["CTR"] = pd.to_numeric(cols["CTR"], errors="coerce")

        # Eliminar filas con valores faltantes
        filtradas = cols.dropna(subset=["Ranking ASIN", "Impresiones", "CTR"])
        filtradas = filtradas[filtradas["Ranking ASIN"] > rango]

        st.dataframe(filtradas.reset_index(drop=True))
