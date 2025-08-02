import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt

st.set_page_config(page_title="Optimización de Listado", layout="wide")

# --- Funciones ---
def extract_mining_title(title_string):
    """Extrae el keyword principal del texto en la primera fila de la pestaña MiningKW."""
    if not isinstance(title_string, str):
        return "Título no encontrado"
    match = re.search(r'US-(.*?)(?:\(|$|-)', title_string)
    if match:
        return match.group(1).strip()
    return "Título no pudo ser extraído"

def inicializar_datos(archivo_subido):
    """Carga los datos del Excel y los guarda en el session_state."""
    try:
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)
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

        if 'MiningUnique' in xls.sheet_names:
            st.session_state.df_mining_unique = pd.read_excel(archivo_subido, sheet_name="MiningUnique", header=0)
        else:
            st.session_state.df_mining_unique = pd.DataFrame()

        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error al leer las pestañas del archivo: {e}")
        st.session_state.datos_cargados = False
def anadir_palabra_a_avoids(palabra, categoria):
    avoids_df = st.session_state.avoids_df
    last_idx = avoids_df[categoria].last_valid_index()
    target_idx = 0 if last_idx is None else last_idx + 1

    if target_idx >= len(avoids_df):
        new_row = pd.DataFrame([[pd.NA] * len(avoids_df.columns)], columns=avoids_df.columns)
        st.session_state.avoids_df = pd.concat([avoids_df, new_row], ignore_index=True)

    st.session_state.avoids_df.loc[target_idx, categoria] = palabra

def mostrar_pagina_categorizacion():
    with st.container(border=True):
        st.subheader("Categorizar Palabras para Añadir a Avoids")
        palabras = st.session_state.get('palabras_para_categorizar', [])

        if not palabras:
            st.session_state.show_categorization_form = False
            st.rerun()
            return

        avoid_column_names = st.session_state.avoids_df.columns.tolist()
        with st.form("form_categorizacion"):
            for palabra in palabras:
                cols = st.columns([2, 3])
                cols[0].write(f"**{palabra}**")
                cols[1].selectbox("Categoría", avoid_column_names, key=f"cat_{palabra}", label_visibility="collapsed")

            submitted = st.form_submit_button("Confirmar y Añadir Palabras")
            if submitted:
                for palabra in palabras:
                    categoria = st.session_state[f"cat_{palabra}"]
                    anadir_palabra_a_avoids(palabra, categoria)

                st.success("¡Palabras añadidas correctamente!")
                st.session_state.show_categorization_form = False
                del st.session_state.palabras_para_categorizar
                st.rerun()

        if st.button("Cancelar"):
            st.session_state.show_categorization_form = False
            del st.session_state.palabras_para_categorizar
            st.rerun()

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
                    marketplace = row.iloc[0]
                    asin = row.iloc[1]
                    titulo = row.iloc[2]
                    bullets = row.iloc[3]
                    descripcion_raw = row.iloc[4]

                    descripcion = descripcion_raw if pd.notna(descripcion_raw) else "Este ASIN tiene contenido A+"

                    with st.expander(f"ASIN: {asin}"):
                        st.markdown(f"**Marketplace:** {marketplace}")
                        st.markdown(f"**Titulo:** {titulo}")
                        st.markdown("**Bullet Points:**")
                        st.write(bullets)
                        st.markdown("**Descripción:**")
                        st.write(descripcion)
                except IndexError:
                    continue

            st.subheader("Reverse ASIN del Producto")
            disable_filter_cliente = st.checkbox("Deshabilitar filtro", key="cliente_disable")
            opciones_clicks = {"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025}
            seleccion_clicks = st.selectbox("ASIN Click Share >:", list(opciones_clicks.keys()), disabled=disable_filter_cliente)
            umbral_clicks = opciones_clicks[seleccion_clicks]

            df_kw_proc = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
            df_kw_proc.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]
            df_kw_proc["ASIN Click Share"] = pd.to_numeric(df_kw_proc["ASIN Click Share"], errors='coerce')

            if not disable_filter_cliente:
                df_kw_filtrado = df_kw_proc[df_kw_proc["ASIN Click Share"].fillna(0) > umbral_clicks].copy()
            else:
                df_kw_filtrado = df_kw_proc.copy()

            df_kw_filtrado["ASIN Click Share"] = (df_kw_filtrado["ASIN Click Share"] * 100).round(2).astype(str) + "%"
            df_kw_filtrado["Search Volume"] = pd.to_numeric(df_kw_filtrado["Search Volume"], errors='coerce').fillna(0).astype(int)
            df_kw_filtrado["Total Click Share"] = (pd.to_numeric(df_kw_filtrado["Total Click Share"], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'

            st.metric("Total de Términos (Cliente)", len(df_kw_filtrado))
            st.dataframe(df_kw_filtrado.reset_index(drop=True), height=400)

        # --- Datos de Competidores ---
        with st.expander("Datos de competidores", expanded=False):
            st.subheader("Reverse ASIN Competidores")
            disable_filter_competidores = st.checkbox("Deshabilitar filtro", key="comp_disable")
            rango = st.selectbox("Sample Product Depth >:", [4, 5, 6], index=1, disabled=disable_filter_competidores)

            df_comp_data_proc = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
            df_comp_data_proc.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
            df_comp_data_proc = df_comp_data_proc.dropna(subset=["Search Terms"])
            df_comp_data_proc['Sample Product Depth'] = pd.to_numeric(df_comp_data_proc['Sample Product Depth'], errors='coerce')

            if not disable_filter_competidores:
                df_comp_data_proc = df_comp_data_proc[df_comp_data_proc["Sample Product Depth"] > rango].copy()

            df_comp_data_proc['Search Volume'] = pd.to_numeric(df_comp_data_proc['Search Volume'], errors='coerce').fillna(0).astype(int)
            df_comp_data_proc['Sample Click Share'] = (pd.to_numeric(df_comp_data_proc['Sample Click Share'], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'
            df_comp_data_proc['Niche Click Share'] = (pd.to_numeric(df_comp_data_proc['Niche Click Share'], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'

            st.metric("Total de Términos (Competidores)", len(df_comp_data_proc))
            st.dataframe(df_comp_data_proc.reset_index(drop=True), height=400)

        # --- Datos de Minería ---
        if st.session_state.get('df_mining_kw') is not None and not st.session_state.df_mining_kw.empty:
            with st.expander("Minería de Search Terms", expanded=False):
                st.markdown(f"#### Keyword Principal: *{st.session_state.mining_title}*")
                disable_filter_mining = st.checkbox("Deshabilitar filtro", key="mining_disable")
                opciones_rel = [30, 50]
                umbral_rel = st.selectbox("Relevance ≥:", opciones_rel, disabled=disable_filter_mining)

                df_mining_proc = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
                df_mining_proc.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']
                df_mining_proc['Relevance'] = pd.to_numeric(df_mining_proc['Relevance'], errors='coerce').fillna(0)

                if not disable_filter_mining:
                    df_to_display = df_mining_proc[df_mining_proc['Relevance'] >= umbral_rel].copy()
                else:
                    df_to_display = df_mining_proc.copy()

                df_to_display['Niche Click Share'] = (pd.to_numeric(df_to_display['Niche Click Share'], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'

                st.metric("Total de Términos (Minería)", len(df_to_display))
                st.dataframe(df_to_display)
        # --- Palabras Únicas ---
        with st.expander("Palabras Únicas", expanded=False):
            # Pega aquí tu bloque de Palabras Únicas tal como lo tienes en tu código actual.

    # --- Tabla Maestra de Datos Compilados ---
    st.subheader("Tabla Maestra de Datos Compilados")
    df_cust = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
    df_cust.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]
    df_cust['Source'] = 'Cliente'

    df_comp = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
    df_comp.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
    df_comp['Source'] = 'Competencia'

    df_mining = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
    df_mining.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']
    df_mining['Source'] = 'Mining'

    df_master = pd.concat([df_cust, df_comp, df_mining], ignore_index=True, sort=False)
    numeric_cols = ['Search Volume', 'ASIN Click Share', 'Total Click Share', 'Sample Click Share', 'Niche Click Share', 'Sample Product Depth', 'Niche Product Depth', 'Relevance']
    for col in numeric_cols:
        if col in df_master.columns:
            df_master[col] = pd.to_numeric(df_master[col], errors='coerce')

    percent_cols = ['ASIN Click Share', 'Total Click Share', 'Sample Click Share', 'Niche Click Share']
    for col in percent_cols:
        if col in df_master.columns:
            mask = df_master[col].notna()
            df_master.loc[mask, col] = (df_master.loc[mask, col] * 100).round(2).astype(str) + '%'

    column_order = [
        'Search Terms', 'Source', 'Search Volume',
        'ASIN Click Share', 'Sample Click Share', 'Niche Click Share', 'Total Click Share',
        'Sample Product Depth', 'Niche Product Depth', 'Relevance'
    ]
    existing_cols = [col for col in column_order if col in df_master.columns]
    df_master = df_master[existing_cols].fillna('N/A')

    st.metric("Total de Registros Compilados", len(df_master))
    st.dataframe(df_master, height=500)
