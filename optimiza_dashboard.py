import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Optimización de Listado", layout="wide")

# --- Funciones de Lógica de Datos ---
def extract_mining_title(title_string):
    if not isinstance(title_string, str): return "Título no encontrado"
    match = re.search(r'US-(.*?)(?:\(|$|-)', title_string)
    return match.group(1).strip() if match else "Título no pudo ser extraído"

def inicializar_datos(archivo_subido):
    try:
        xls = pd.ExcelFile(archivo_subido)
        # Carga 100% posicional, ignorando todos los encabezados del archivo.
        st.session_state.df_asin = pd.read_excel(xls, sheet_name="CustListing", header=None, skiprows=1)
        st.session_state.avoids_df = pd.read_excel(xls, sheet_name="Avoids", header=None, skiprows=1)
        st.session_state.df_cust_unique = pd.read_excel(xls, sheet_name="CustUnique", header=None, skiprows=1)
        st.session_state.df_comp_unique = pd.read_excel(xls, sheet_name="CompUnique", header=None, skiprows=1)
        st.session_state.df_kw = pd.read_excel(xls, sheet_name="CustKW", header=None, skiprows=2)
        st.session_state.df_comp_data = pd.read_excel(xls, sheet_name="CompKW", header=None, skiprows=2)
        
        st.session_state.df_mining_kw = pd.read_excel(xls, sheet_name="MiningKW", header=None, skiprows=2) if 'MiningKW' in xls.sheet_names else pd.DataFrame()
        st.session_state.df_mining_unique = pd.read_excel(xls, sheet_name="MiningUnique", header=None, skiprows=1) if 'MiningUnique' in xls.sheet_names else pd.DataFrame()
        
        if 'MiningKW' in xls.sheet_names:
            mining_kw_raw = pd.read_excel(xls, sheet_name="MiningKW", header=None)
            st.session_state.mining_title = extract_mining_title(mining_kw_raw.iloc[0, 0]) if not mining_kw_raw.empty else ""
        else:
            st.session_state.mining_title = ""
        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error fatal al leer el archivo. Verifica que las pestañas existan. Error: {e}")
        st.session_state.datos_cargados = False

def anadir_palabra_a_avoids(palabra, categoria_idx):
    avoids_df = st.session_state.avoids_df
    last_idx = avoids_df.iloc[:, categoria_idx].last_valid_index()
    target_idx = 0 if pd.isna(last_idx) else last_idx + 1
    
    if target_idx >= len(avoids_df):
        new_row = pd.DataFrame([[pd.NA] * len(avoids_df.columns)])
        st.session_state.avoids_df = pd.concat([avoids_df, new_row], ignore_index=True)
    st.session_state.avoids_df.iloc[target_idx, categoria_idx] = palabra

def mostrar_pagina_categorizacion():
    with st.container(border=True):
        st.subheader("Categorizar Palabras")
        palabras = st.session_state.get('palabras_para_categorizar', [])
        if not palabras:
            st.session_state.show_categorization_form = False
            st.rerun()
        
        avoid_categorias = {'Stopword': 0, 'Marca': 1, 'Irrelevante': 2}
        with st.form("form_categorizacion"):
            for palabra in palabras:
                st.selectbox(f"Categoría para **'{palabra}'**", list(avoid_categorias.keys()), key=f"cat_{palabra}")
            
            if st.form_submit_button("Confirmar y Añadir"):
                for palabra in palabras:
                    categoria_nombre = st.session_state[f"cat_{palabra}"]
                    categoria_idx = avoid_categorias[categoria_nombre]
                    anadir_palabra_a_avoids(palabra, categoria_idx)
                st.success("¡Palabras añadidas!")
                st.session_state.show_categorization_form = False
                del st.session_state.palabras_para_categorizar
                st.rerun()
        if st.button("Cancelar"):
            st.session_state.show_categorization_form = False
            del st.session_state.palabras_para_categorizar
            st.rerun()

# --- Interfaz Principal ---
st.title("📊 Dashboard de Optimización de Listado")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if 'datos_cargados' not in st.session_state:
    st.session_state.datos_cargados = False

if archivo and (st.session_state.get('last_uploaded_file') != archivo.name):
    st.session_state.last_uploaded_file = archivo.name
    inicializar_datos(archivo)

if st.session_state.datos_cargados:
    tab1, tab2, tab3, tab4 = st.tabs(["Análisis de Fuentes", "Palabras Únicas", "Tabla Maestra", "Info ASINs"])

    with tab1:
        st.header("Análisis de Fuentes de Keywords")
        with st.container(border=True):
            st.subheader("Cliente: Reverse ASIN del Producto")
            disable_filter_cliente = st.checkbox("Mostrar todos", key="cliente_disable")
            umbral_clicks = st.selectbox("ASIN Click Share >:", [0.05, 0.025], format_func=lambda x: f"{x:.1%}", disabled=disable_filter_cliente)
            df_kw_proc = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
            df_kw_proc.iloc[:, 1] = pd.to_numeric(df_kw_proc.iloc[:, 1], errors='coerce')
            df_kw_filtrado = df_kw_proc if disable_filter_cliente else df_kw_proc[df_kw_proc.iloc[:, 1].fillna(0) > umbral_clicks]
            st.metric("Total de Términos (Cliente)", len(df_kw_filtrado))
            st.dataframe(df_kw_filtrado)

        with st.container(border=True):
            st.subheader("Competidores: Reverse ASIN")
            disable_filter_competidores = st.checkbox("Mostrar todos", key="comp_disable")
            rango = st.selectbox("Sample Product Depth >:", [4, 5, 6], index=1, disabled=disable_filter_competidores)
            df_comp_proc = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
            df_comp_proc.iloc[:, 2] = pd.to_numeric(df_comp_proc.iloc[:, 2], errors='coerce')
            df_comp_filtrado = df_comp_proc if disable_filter_competidores else df_comp_proc[df_comp_proc.iloc[:, 2].notna() & (df_comp_proc.iloc[:, 2] > rango)]
            st.metric("Total de Términos (Competidores)", len(df_comp_filtrado))
            st.dataframe(df_comp_filtrado)

        if not st.session_state.df_mining_kw.empty:
            with st.container(border=True):
                st.subheader(f"Minería de Search Terms: *{st.session_state.mining_title}*")
                disable_filter_mining = st.checkbox("Mostrar todos", key="mining_disable")
                umbral_rel = st.selectbox("Relevance ≥:", [30, 50], disabled=disable_filter_mining)
                df_mining_proc = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
                df_mining_proc.iloc[:, 1] = pd.to_numeric(df_mining_proc.iloc[:, 1], errors='coerce').fillna(0)
                df_mining_filtrado = df_mining_proc if disable_filter_mining else df_mining_proc[df_mining_proc.iloc[:, 1] >= umbral_rel]
                st.metric("Total de Términos (Minería)", len(df_mining_filtrado))
                st.dataframe(df_mining_filtrado)

    with tab2:
        st.header("Gestión de Palabras Únicas y Exclusiones")
        if st.session_state.get('show_categorization_form', False): mostrar_pagina_categorizacion()
        
        with st.container(border=True):
            st.subheader("Palabras en Lista de Exclusión ('Avoids')")
            st.dataframe(st.session_state.avoids_df.fillna(''))

        with st.container(border=True):
            st.subheader("Tabla Consolidada de Palabras Únicas")
            umbral_freq = st.selectbox("Frecuencia Mínima ≥:", [1, 2, 3, 4, 5], index=1)

            df_cust_u = st.session_state.df_cust_unique.iloc[:, [0, 1]].copy()
            df_comp_u = st.session_state.df_comp_unique.iloc[:, [0, 1]].copy()
            
            final_df_u = pd.merge(df_cust_u, df_comp_u, on=0, how='outer', suffixes=('_Cliente', '_Comp'))
            if not st.session_state.df_mining_unique.empty:
                df_mining_u = st.session_state.df_mining_unique.iloc[:, [0, 1]].copy()
                final_df_u = pd.merge(final_df_u, df_mining_u, on=0, how='outer')

            final_df_u = final_df_u.fillna(0)
            freq_cols_indices = [i for i, col in enumerate(final_df_u.columns) if isinstance(col, str) and col.startswith('1_') or col == 1]
            for col_idx in freq_cols_indices:
                final_df_u.iloc[:, col_idx] = pd.to_numeric(final_df_u.iloc[:, col_idx], errors='coerce').fillna(0).astype(int)
            
            avoid_list = pd.concat([st.session_state.avoids_df.iloc[:, i] for i in range(st.session_state.avoids_df.shape[1])]).dropna().unique()
            df_filtered_u = final_df_u[~final_df_u.iloc[:, 0].isin(avoid_list)]
            df_filtered_u = df_filtered_u[df_filtered_u.iloc[:, freq_cols_indices].ge(umbral_freq).any(axis=1)].copy()

            if not df_filtered_u.empty:
                df_filtered_u.insert(0, "Seleccionar", False)
                # **EXCEPCIÓN NECESARIA**: Asignar nombres temporales solo para mostrar en el data_editor
                temp_col_names = ["Seleccionar", "Keyword", "Frec. Cliente", "Frec. Comp."]; 
                if len(df_filtered_u.columns) > 4: temp_col_names.append("Frec. Mining")
                # Asegurar que la lista de nombres coincida con el número de columnas
                temp_col_names = temp_col_names[:len(df_filtered_u.columns)]
                df_filtered_u.columns = temp_col_names

                st.metric("Total de Palabras Únicas", len(df_filtered_u))
                edited_df = st.data_editor(df_filtered_u, hide_index=True, key="editor_palabras_unicas")

                if st.button("Añadir seleccionadas a Avoids"):
                    palabras_a_anadir = edited_df.loc[edited_df["Seleccionar"], "Keyword"].tolist()
                    if palabras_a_anadir:
                        st.session_state.palabras_para_categorizar = palabras_a_anadir
                        st.session_state.show_categorization_form = True; st.rerun()
                    else: st.warning("No has seleccionado ninguna palabra.")
            else: st.info("No hay palabras para mostrar.")

    with tab3:
        st.header("Tabla Maestra de Datos Compilados")
        df_cust = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].assign(Source='Cliente')
        df_comp = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].assign(Source='Competencia')
        df_master = pd.concat([df_cust, df_comp], ignore_index=True)
        if not st.session_state.df_mining_kw.empty:
            df_mining = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].assign(Source='Mining')
            df_master = pd.concat([df_master, df_mining], ignore_index=True)
        st.metric("Total de Registros Compilados", len(df_master))
        st.dataframe(df_master.fillna('N/A'))
    
    with tab4:
        st.header("Información de Listings")
        with st.container(border=True):
            st.subheader("ASINs de Cliente")
            for index, row in st.session_state.df_asin.iterrows():
                with st.expander(f"ASIN: {row.iloc[1]}"):
                    st.write(f"**Marketplace:** {row.iloc[0]}")
                    st.write(f"**Título:** {row.iloc[2]}")
                    st.write(f"**Bullet Points:** {row.iloc[3]}")
                    st.write(f"**Descripción:** {row.iloc[4] if pd.notna(row.iloc[4]) and str(row.iloc[4]).strip() else 'Contenido A+'}")
            st.subheader("ASINs de Competidores")
            df_comp_asins_raw = pd.read_excel(archivo, sheet_name="CompKW", header=None)
            asin_raw = str(df_comp_asins_raw.iloc[0, 0])
            start_index = asin_raw.find('B0')
            clean_string_block = asin_raw[start_index:] if start_index != -1 else ""
            clean_asin_list = [asin.split('-')[0].strip() for asin in clean_string_block.split(',') if 'B0' in asin]
            st.dataframe(pd.DataFrame({ "ASIN Competidor": clean_asin_list }))