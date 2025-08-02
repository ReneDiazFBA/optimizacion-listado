import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt

st.set_page_config(page_title="Optimización de Listado", layout="wide")

# --- Funciones ---
def extract_mining_title(title_string):
    if not isinstance(title_string, str):
        return "Título no encontrado"
    match = re.search(r'US-(.*?)(?:\(|$|-)', title_string)
    if match:
        return match.group(1).strip()
    return "Título no pudo ser extraído"

def inicializar_datos(archivo_subido):
    try:
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW", header=None, skiprows=2)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None, skiprows=2)
        xls = pd.ExcelFile(archivo_subido)
        if 'MiningKW' in xls.sheet_names:
            mining_kw_raw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None)
            title_string = mining_kw_raw.iloc[0, 0] if not mining_kw_raw.empty else ""
            st.session_state.mining_title = extract_mining_title(title_string)
            st.session_state.df_mining_kw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None, skiprows=2)
        else:
            st.session_state.df_mining_kw = pd.DataFrame()
            st.session_state.mining_title = ""
        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        st.session_state.datos_cargados = False

# --- Lógica Principal ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

    if st.session_state.get('datos_cargados', False):
        with st.expander("Datos para Análisis", expanded=False):

            # --- Datos del Cliente ---
            with st.expander("Datos del cliente", expanded=False):
                st.subheader("Listing de ASIN")
                for index, row in st.session_state.df_asin.iterrows():
                    try:
                        asin = row.iloc[1]
                        titulo = row.iloc[2]
                        bullets = row.iloc[3]
                        descripcion = row.iloc[4] if pd.notna(row.iloc[4]) else "Este ASIN tiene contenido A+"
                        with st.expander(f"ASIN: {asin}"):
                            st.markdown(f"**Titulo:** {titulo}")
                            st.markdown("**Bullet Points:**")
                            st.write(bullets)
                            st.markdown("**Descripción:**")
                            st.write(descripcion)
                    except IndexError:
                        continue

                st.subheader("Reverse ASIN del Producto")
                opciones_clicks = {"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025}
                seleccion_clicks = st.selectbox("ASIN Click Share >:", list(opciones_clicks.keys()))
                umbral_clicks = opciones_clicks[seleccion_clicks]

                df_kw_proc = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
                df_kw_proc.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]

                df_kw_proc["ASIN Click Share"] = pd.to_numeric(df_kw_proc["ASIN Click Share"], errors='coerce')
                df_kw_filtrado = df_kw_proc[df_kw_proc["ASIN Click Share"].fillna(0) > umbral_clicks].copy()

                df_kw_filtrado["ASIN Click Share"] = (df_kw_filtrado["ASIN Click Share"] * 100).round(2).astype(str) + "%"
                df_kw_filtrado["Search Volume"] = pd.to_numeric(df_kw_filtrado["Search Volume"], errors='coerce').fillna(0).astype(int)
                df_kw_filtrado["Total Click Share"] = (pd.to_numeric(df_kw_filtrado["Total Click Share"], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'

                df_kw_filtrado = df_kw_filtrado[["Search Terms", "Search Volume", "ASIN Click Share", "Total Click Share"]]
                df_kw_filtrado_reset = df_kw_filtrado.reset_index(drop=True)
                df_kw_filtrado_reset.insert(0, '#', range(1, 1 + len(df_kw_filtrado_reset)))

                with st.expander("Ver/Ocultar Reverse ASIN del Producto", expanded=True):
                    st.dataframe(df_kw_filtrado_reset, height=400)

            # --- Datos de Competidores ---
            with st.expander("Datos de competidores", expanded=False):
                st.subheader("Reverse ASIN Competidores")
                rango = st.selectbox("Sample Product Depth >:", [4, 5, 6], index=1)

                df_comp_data_proc = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
                df_comp_data_proc.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
                df_comp_data_proc = df_comp_data_proc.dropna(subset=["Search Terms"])

                df_comp_data_proc['Search Volume'] = pd.to_numeric(df_comp_data_proc['Search Volume'], errors='coerce').fillna(0).astype(int)
                df_comp_data_proc['Sample Click Share'] = (pd.to_numeric(df_comp_data_proc['Sample Click Share'], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'
                df_comp_data_proc['Niche Click Share'] = (pd.to_numeric(df_comp_data_proc['Niche Click Share'], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'
                df_comp_data_proc['Sample Product Depth'] = pd.to_numeric(df_comp_data_proc['Sample Product Depth'], errors='coerce')
                df_comp_data_proc = df_comp_data_proc[df_comp_data_proc["Sample Product Depth"] > rango]

                df_comp_data_proc = df_comp_data_proc[["Search Terms", "Search Volume", "Sample Click Share", "Niche Click Share", "Sample Product Depth"]]
                df_comp_data_proc_reset = df_comp_data_proc.reset_index(drop=True)
                df_comp_data_proc_reset.insert(0, '#', range(1, 1 + len(df_comp_data_proc_reset)))

                with st.expander("Ver/Ocultar Reverse ASIN Competidores", expanded=True):
                    st.dataframe(df_comp_data_proc_reset, height=400)

            # --- Datos de Minería ---
            if not st.session_state.df_mining_kw.empty:
                with st.expander("Mineria de Search Terms", expanded=False):
                    st.markdown(f"#### Keyword Principal: *{st.session_state.mining_title}*")
                    opciones_rel = [30, 50]
                    umbral_rel = st.selectbox("Relevance ≥:", opciones_rel)

                    df_mining_proc = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
                    df_mining_proc.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']

                    df_mining_proc['Relevance'] = pd.to_numeric(df_mining_proc['Relevance'], errors='coerce').fillna(0)
                    df_to_display = df_mining_proc[df_mining_proc['Relevance'] >= umbral_rel].copy()
                    df_to_display['Niche Click Share'] = (pd.to_numeric(df_to_display['Niche Click Share'], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'

                    df_to_display_reset = df_to_display.reset_index(drop=True)
                    df_to_display_reset.insert(0, '#', range(1, 1 + len(df_to_display_reset)))

                    with st.expander("Ver/Ocultar Tabla de Minería", expanded=True):
                        st.dataframe(df_to_display_reset)
