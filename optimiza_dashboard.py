
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
        avoids = pd.read_excel(archivo, sheet_name="Avoids")
        df_cust_unique = pd.read_excel(archivo, sheet_name="CustUnique")
        df_comp_unique = pd.read_excel(archivo, sheet_name="CompUnique")
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        st.stop()

    # DATOS DEL CLIENTE
    with st.expander("Datos del cliente", expanded=False):
        subtabs = st.radio("Selecciona una vista:", ["Listado de ASINs", "Palabras Clave (Keywords)"])

        if subtabs == "Listado de ASINs":
            for _, row in df_asin.iterrows():
                asin = row.get("ASIN", "")
                titulo = row.get("Product Title", "")
                bullets = row.get("Bullet Points", "")
                descripcion = row.get("Description", "")
                with st.expander(f"ASIN: {asin}"):
                    st.markdown("**Título del producto:**")
                    st.write(titulo)
                    st.markdown("**Puntos clave:**")
                    st.write(bullets)
                    if pd.notna(descripcion) and str(descripcion).strip():
                        st.markdown("**Descripción:**")
                        st.write(descripcion)

        elif subtabs == "Palabras Clave (Keywords)":
            opciones = {"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025}
            seleccion = st.selectbox("Filtrar por porcentaje de clics:", list(opciones.keys()))
            umbral = opciones[seleccion]
            df_kw["Click Share"] = pd.to_numeric(df_kw["Click Share"], errors="coerce")
            df_kw_filtrado = df_kw[df_kw["Click Share"].fillna(0) > umbral].copy()
            df_kw_filtrado["Click Share"] = (df_kw_filtrado["Click Share"] * 100).round(2).astype(str) + "%"
            df_kw_filtrado["M. Searches"] = pd.to_numeric(df_kw_filtrado["M. Searches"], errors="coerce").fillna(0).astype(int)
            columnas = ["Keyword", "M. Searches", "Click Share"]
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
            st.dataframe(df_kw_filtrado[columnas].style.set_properties(**{
                "white-space": "normal", "word-wrap": "break-word"
            }))
            st.markdown("</div>", unsafe_allow_html=True)

    # DATOS DE COMPETIDORES
    with st.expander("Datos de competidores", expanded=False):
        st.subheader("ASIN de competidores")
        asin_raw = str(df_comp.iloc[0, 0])
        if "ExpandKeywords" in asin_raw:
            cuerpo = asin_raw.replace("ExpandKeywords(439)-US-", "").split("-Last-30-days")[0]
            asin_list = [a.strip() for a in cuerpo.split(",") if a.strip()]
            df_asin_comp = pd.DataFrame({"ASIN de competidor": asin_list})
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
            st.dataframe(df_asin_comp.style.set_properties(**{
                "white-space": "normal", "word-wrap": "break-word"
            }))
            st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("Keywords por ranking de competidor")
        rango = st.selectbox("Mostrar keywords con ranking mayor a:", [4, 5, 6], index=1)
        df_comp_data.replace(r'^\s*$', pd.NA, regex=True, inplace=True)
        cols = df_comp_data.iloc[:, [0, 5, 8, 18]].copy()
        cols.columns = ["Palabra clave", "Ranking ASIN", "Impresiones", "CTR"]
        cols = cols.dropna()
        cols = cols[pd.to_numeric(cols["Ranking ASIN"], errors="coerce") > rango]
        st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
        st.dataframe(cols.reset_index(drop=True).style.set_properties(**{
            "white-space": "normal", "word-wrap": "break-word"
        }))
        st.markdown("</div>", unsafe_allow_html=True)

    # LISTA AVOIDS
    st.subheader("Palabras en lista de exclusión ('Avoids')")
    col1, col2, col3 = st.columns(3)
    col1.markdown("**Stopwords**")
    col1.dataframe(avoids.iloc[:, 0].dropna().reset_index(drop=True))
    col2.markdown("**Marcas**")
    col2.dataframe(avoids.iloc[:, 1].dropna().reset_index(drop=True))
    col3.markdown("**Irrelevantes**")
    col3.dataframe(avoids.iloc[:, 2].dropna().reset_index(drop=True))

    # PALABRAS ÚNICAS
    st.subheader("Palabras únicas del cliente")
    filtro_cust = st.checkbox("Ocultar frecuencia ≤ 2", value=True, key="fc")
    df_cust = df_cust_unique.rename(columns=lambda c: c.strip().capitalize())
    if filtro_cust:
        df_cust = df_cust[df_cust["Frequency"] > 2]
    st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
    st.dataframe(df_cust.reset_index(drop=True).style.set_properties(**{
        "white-space": "normal", "word-wrap": "break-word"
    }))
    st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Palabras únicas de competidores")
    filtro_comp = st.checkbox("Ocultar frecuencia ≤ 2 (competidores)", value=True, key="fc2")
    df_comp = df_comp_unique.rename(columns=lambda c: c.strip().capitalize())
    if filtro_comp:
        df_comp = df_comp[df_comp["Frequency"] > 2]
    st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
    st.dataframe(df_comp.reset_index(drop=True).style.set_properties(**{
        "white-space": "normal", "word-wrap": "break-word"
    }))
    st.markdown("</div>", unsafe_allow_html=True)

    # NUEVAS PALABRAS
    st.subheader("Agregar nuevas palabras a Avoids")
    nueva_palabra = st.text_input("Escribe una palabra nueva:")
    categoria = st.selectbox("Categoría", ["Stopword", "Marca", "Irrelevante"])
    if st.button("Agregar a lista temporal"):
        if "nuevas_avoids" not in st.session_state:
            st.session_state["nuevas_avoids"] = []
        st.session_state["nuevas_avoids"].append((nueva_palabra.strip(), categoria))

    if "nuevas_avoids" in st.session_state and st.session_state["nuevas_avoids"]:
        st.markdown("### Palabras nuevas seleccionadas:")
        df_nuevas = pd.DataFrame(st.session_state["nuevas_avoids"], columns=["Palabra", "Categoría"])
        st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
        st.dataframe(df_nuevas.style.set_properties(**{
            "white-space": "normal", "word-wrap": "break-word"
        }))
        st.markdown("</div>", unsafe_allow_html=True)
