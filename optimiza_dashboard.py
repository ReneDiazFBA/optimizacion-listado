
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Optimización de Listado", layout="wide")
st.title("Optimización de Listado - Dashboard")

# --- Funciones Auxiliares ---
def inicializar_datos(archivo_subido):
    """Carga los datos del Excel y los guarda en el session_state."""
    try:
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW")
        st.session_state.df_comp = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", skiprows=2)

        avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=None)
        avoids_df.columns = ["Stopword", "Marca", "Irrelevante"]
        st.session_state.avoids_df = avoids_df

        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique")
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique")
        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        st.session_state.datos_cargados = False

archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo and not st.session_state.get('datos_cargados', False):
    inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):

    with st.expander("Datos del cliente", expanded=False):
        subtabs = st.radio("Selecciona una vista:", ["Listado de ASINs", "Palabras Clave (Keywords)"], key="cliente_radio")

        if subtabs == "Listado de ASINs":
            for _, row in st.session_state.df_asin.iterrows():
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
            df_kw_copy = st.session_state.df_kw.copy()
            df_kw_copy["Click Share"] = pd.to_numeric(df_kw_copy["Click Share"], errors="coerce")
            df_kw_filtrado = df_kw_copy[df_kw_copy["Click Share"].fillna(0) > umbral]
            df_kw_filtrado["Click Share"] = (df_kw_filtrado["Click Share"] * 100).round(2).astype(str) + "%"
            df_kw_filtrado["M. Searches"] = pd.to_numeric(df_kw_filtrado["M. Searches"], errors="coerce").fillna(0).astype(int)
            columnas = ["Keyword", "M. Searches", "Click Share"]
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
            st.dataframe(df_kw_filtrado[columnas].reset_index(drop=True).style.set_properties(**{
                "white-space": "normal", "word-wrap": "break-word"
            }))
            st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Datos de competidores", expanded=False):
        st.subheader("ASIN de competidores")
        asin_raw = str(st.session_state.df_comp.iloc[0, 0])
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
        df_comp_data_copy = st.session_state.df_comp_data.copy()
        df_comp_data_copy.replace(r'^\s*$', pd.NA, regex=True, inplace=True)
        cols = df_comp_data_copy.iloc[:, [0, 5, 8, 18]].copy()
        cols.columns = ["Palabra clave", "Ranking ASIN", "Impresiones", "CTR"]
        cols = cols.dropna()
        cols['Ranking ASIN'] = pd.to_numeric(cols['Ranking ASIN'], errors='coerce')
        cols = cols[cols["Ranking ASIN"].notna() & (cols["Ranking ASIN"] > rango)]
        st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
        st.dataframe(cols.reset_index(drop=True).style.set_properties(**{
            "white-space": "normal", "word-wrap": "break-word"
        }))
        st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Agregar nuevas palabras a Avoids")
    with st.form(key="avoid_form"):
        nueva_palabra = st.text_input("Escribe una palabra nueva:")
        categoria = st.selectbox("Categoría", ["Stopword", "Marca", "Irrelevante"])
        submitted = st.form_submit_button("Agregar a Avoids")

        if submitted and nueva_palabra:
            avoids_df = st.session_state.avoids_df
            last_idx = avoids_df[categoria].last_valid_index()
            target_idx = 0 if last_idx is None else last_idx + 1
            if target_idx >= len(avoids_df):
                nueva_fila_df = pd.DataFrame([[pd.NA, pd.NA, pd.NA]], columns=avoids_df.columns)
                st.session_state.avoids_df = pd.concat([avoids_df, nueva_fila_df], ignore_index=True)
            st.session_state.avoids_df.loc[target_idx, categoria] = nueva_palabra
            st.success(f"Palabra '{nueva_palabra}' agregada a '{categoria}'.")

    st.subheader("Palabras en lista de exclusión ('Avoids')")
    col1, col2, col3 = st.columns(3)
    avoids_display = st.session_state.avoids_df
    with col1:
        st.markdown("**Stopwords**")
        st.dataframe(avoids_display["Stopword"].dropna().reset_index(drop=True), use_container_width=True)
    with col2:
        st.markdown("**Marcas**")
        st.dataframe(avoids_display["Marca"].dropna().reset_index(drop=True), use_container_width=True)
    with col3:
        st.markdown("**Irrelevantes**")
        st.dataframe(avoids_display["Irrelevante"].dropna().reset_index(drop=True), use_container_width=True)
