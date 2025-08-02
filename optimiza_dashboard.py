import streamlit as st
import pandas as pd
import re

# Configuración de la página al principio del script
st.set_page_config(page_title="Optimización de Listado", layout="wide")

# --- Funciones de Lógica de Datos ---
def extract_mining_title(title_string):
    """Extrae el keyword principal del texto en la primera fila de la pestaña MiningKW."""
    if not isinstance(title_string, str):
        return "Título no encontrado"
    match = re.search(r'US-(.*?)(?:\(|$|-)', title_string)
    return match.group(1).strip() if match else "Título no pudo ser extraído"

def inicializar_datos(archivo_subido):
    """Carga los datos del Excel y los guarda en el session_state."""
    try:
        xls = pd.ExcelFile(archivo_subido)
        # --- INICIO DE LA SECCIÓN CORREGIDA ---
        # Carga robusta que ignora los encabezados del archivo y asigna los suyos.
        
        # Pestañas requeridas
        st.session_state.df_asin = pd.read_excel(xls, sheet_name="CustListing", header=None, skiprows=1)
        st.session_state.df_asin.columns = ['Marketplace', 'ASIN', 'Product Title', 'Bullet Points', 'Description']

        st.session_state.avoids_df = pd.read_excel(xls, sheet_name="Avoids", header=None, skiprows=1)
        st.session_state.avoids_df.columns = ['Stopword', 'Marca', 'Irrelevante']

        st.session_state.df_cust_unique = pd.read_excel(xls, sheet_name="CustUnique", header=None, skiprows=1)
        st.session_state.df_cust_unique.columns = ['Keyword', 'Frequency']

        st.session_state.df_comp_unique = pd.read_excel(xls, sheet_name="CompUnique", header=None, skiprows=1)
        st.session_state.df_comp_unique.columns = ['Keyword', 'Frequency']

        st.session_state.df_kw = pd.read_excel(xls, sheet_name="CustKW", header=None, skiprows=2)
        st.session_state.df_comp_data = pd.read_excel(xls, sheet_name="CompKW", header=None, skiprows=2)
        
        # Carga segura de pestañas opcionales
        st.session_state.df_mining_kw = pd.read_excel(xls, sheet_name="MiningKW", header=None, skiprows=2) if 'MiningKW' in xls.sheet_names else pd.DataFrame()
        st.session_state.df_mining_unique = pd.read_excel(xls, sheet_name="MiningUnique", header=None, skiprows=1) if 'MiningUnique' in xls.sheet_names else pd.DataFrame()
        if not st.session_state.df_mining_unique.empty:
            st.session_state.df_mining_unique.columns = ['Keyword', 'Frequency']
            
        if 'MiningKW' in xls.sheet_names:
            mining_kw_raw = pd.read_excel(xls, sheet_name="MiningKW", header=None)
            st.session_state.mining_title = extract_mining_title(mining_kw_raw.iloc[0, 0]) if not mining_kw_raw.empty else ""
        else:
            st.session_state.mining_title = ""
        # --- FIN DE LA SECCIÓN CORREGIDA ---
            
        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error al leer el archivo. Asegúrate de que todas las pestañas requeridas existan y tengan datos. Error: {e}")
        st.session_state.datos_cargados = False

def anadir_palabra_a_avoids(palabra, categoria):
    """Añade una palabra a la categoría correcta en el dataframe de Avoids."""
    avoids_df = st.session_state.avoids_df
    if categoria not in avoids_df.columns:
        st.error(f"La categoría '{categoria}' no existe en la tabla de Avoids.")
        return
    
    last_idx = avoids_df[categoria].last_valid_index()
    target_idx = 0 if pd.isna(last_idx) else last_idx + 1
    
    if target_idx >= len(avoids_df):
        new_row = pd.DataFrame([[pd.NA] * len(avoids_df.columns)], columns=avoids_df.columns)
        st.session_state.avoids_df = pd.concat([avoids_df, new_row], ignore_index=True)
    st.session_state.avoids_df.loc[target_idx, categoria] = palabra

def mostrar_pagina_categorizacion():
    """Muestra la interfaz para categorizar las palabras seleccionadas."""
    with st.container(border=True):
        st.subheader("Categorizar Palabras para Añadir a Avoids")
        palabras = st.session_state.get('palabras_para_categorizar', [])
        if not palabras:
            st.session_state.show_categorization_form = False
            st.rerun()
        
        avoid_column_names = st.session_state.avoids_df.columns.tolist()
        with st.form("form_categorizacion"):
            for palabra in palabras:
                st.selectbox(f"Categoría para **'{palabra}'**", avoid_column_names, key=f"cat_{palabra}")
            
            submitted = st.form_submit_button("Confirmar y Añadir")
            if submitted:
                for palabra in palabras:
                    categoria = st.session_state[f"cat_{palabra}"]
                    anadir_palabra_a_avoids(palabra, categoria)
                st.success("¡Palabras añadidas a la lista de exclusión!")
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
            disable_filter_cliente = st.checkbox("Mostrar todos (deshabilitar filtro)", key="cliente_disable")
            opciones_clicks = {"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025}
            seleccion_clicks = st.selectbox("ASIN Click Share >:", list(opciones_clicks.keys()), disabled=disable_filter_cliente)
            umbral_clicks = opciones_clicks[seleccion_clicks]

            df_kw_proc = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
            df_kw_proc.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]
            df_kw_proc["ASIN Click Share"] = pd.to_numeric(df_kw_proc["ASIN Click Share"], errors='coerce')

            df_kw_filtrado = df_kw_proc.copy()
            if not disable_filter_cliente:
                df_kw_filtrado = df_kw_proc[df_kw_proc["ASIN Click Share"].fillna(0) > umbral_clicks]

            df_kw_filtrado["ASIN Click Share"] = (df_kw_filtrado["ASIN Click Share"].fillna(0) * 100).round(2).astype(str) + "%"
            st.metric("Total de Términos (Cliente)", len(df_kw_filtrado))
            st.dataframe(df_kw_filtrado)

        with st.container(border=True):
            st.subheader("Competidores: Reverse ASIN")
            disable_filter_competidores = st.checkbox("Mostrar todos (deshabilitar filtro)", key="comp_disable")
            rango = st.selectbox("Sample Product Depth >:", [4, 5, 6], index=1, disabled=disable_filter_competidores)

            df_comp_proc = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
            df_comp_proc.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
            df_comp_proc = df_comp_proc.dropna(subset=["Search Terms"])
            df_comp_proc['Sample Product Depth'] = pd.to_numeric(df_comp_proc['Sample Product Depth'], errors='coerce')
            
            df_comp_filtrado = df_comp_proc.copy()
            if not disable_filter_competidores:
                df_comp_filtrado = df_comp_proc[df_comp_proc["Sample Product Depth"].notna() & (df_comp_proc["Sample Product Depth"] > rango)]
            
            st.metric("Total de Términos (Competidores)", len(df_comp_filtrado))
            st.dataframe(df_comp_filtrado)

        if not st.session_state.df_mining_kw.empty:
            with st.container(border=True):
                st.subheader(f"Minería de Search Terms: *{st.session_state.mining_title}*")
                disable_filter_mining = st.checkbox("Mostrar todos (deshabilitar filtro)", key="mining_disable")
                umbral_rel = st.selectbox("Relevance ≥:", [30, 50], disabled=disable_filter_mining)

                df_mining_proc = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
                df_mining_proc.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']
                df_mining_proc['Relevance'] = pd.to_numeric(df_mining_proc['Relevance'], errors='coerce').fillna(0)

                df_mining_filtrado = df_mining_proc.copy()
                if not disable_filter_mining:
                    df_mining_filtrado = df_mining_proc[df_mining_proc['Relevance'] >= umbral_rel]
                
                st.metric("Total de Términos (Minería)", len(df_mining_filtrado))
                st.dataframe(df_mining_filtrado)

    with tab2:
        st.header("Gestión de Palabras Únicas y Exclusiones")

        if st.session_state.get('show_categorization_form', False):
            mostrar_pagina_categorizacion()
        
        with st.container(border=True):
            st.subheader("Palabras en Lista de Exclusión ('Avoids')")
            st.dataframe(st.session_state.avoids_df.fillna(''))

        with st.container(border=True):
            st.subheader("Tabla Consolidada de Palabras Únicas")
            umbral_freq = st.selectbox("Frecuencia Mínima ≥:", [1, 2, 3, 4, 5], index=1)

            df_cust_u_proc = st.session_state.df_cust_unique.copy()
            df_comp_u_proc = st.session_state.df_comp_unique.copy()

            final_df_u = pd.merge(df_cust_u_proc, df_comp_u_proc, on='Keyword', how='outer', suffixes=('_Cliente', '_Comp'))
            final_df_u.rename(columns={'Frequency_Cliente': 'Frec. Cliente', 'Frequency_Comp': 'Frec. Comp.'}, inplace=True)
            
            if not st.session_state.df_mining_unique.empty:
                df_mining_u_proc = st.session_state.df_mining_unique.copy()
                final_df_u = pd.merge(final_df_u, df_mining_u_proc.rename(columns={'Frequency': 'Frec. Mining'}), on='Keyword', how='outer')
            
            final_df_u = final_df_u.fillna(0)
            freq_cols = [col for col in final_df_u.columns if 'Frec.' in col]
            for col in freq_cols:
                final_df_u[col] = final_df_u[col].astype(int)

            avoid_list = pd.concat([st.session_state.avoids_df[col] for col in st.session_state.avoids_df.columns]).dropna().unique()
            df_filtered_u = final_df_u[~final_df_u['Keyword'].isin(avoid_list)]
            df_filtered_u = df_filtered_u[df_filtered_u[freq_cols].ge(umbral_freq).any(axis=1)].copy()

            if not df_filtered_u.empty:
                df_filtered_u.insert(0, "Seleccionar", False)
                st.metric("Total de Palabras Únicas", len(df_filtered_u))
                
                edited_df = st.data_editor(df_filtered_u, hide_index=True, key="editor_palabras_unicas")

                if st.button("Añadir seleccionadas a Avoids"):
                    palabras_a_anadir = edited_df.loc[edited_df["Seleccionar"], "Keyword"].tolist()
                    if palabras_a_anadir:
                        st.session_state.palabras_para_categorizar = palabras_a_anadir
                        st.session_state.show_categorization_form = True
                        st.rerun()
                    else:
                        st.warning("No has seleccionado ninguna palabra.")
            else:
                st.info("No hay palabras únicas para mostrar con los filtros actuales.")

    with tab3:
        st.header("Tabla Maestra de Datos Compilados")
        df_cust = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].assign(Source='Cliente')
        df_cust.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share", 'Source']
        df_comp = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].assign(Source='Competencia')
        df_comp.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share", 'Source']
        
        df_master = pd.concat([df_cust, df_comp], ignore_index=True, sort=False)
        
        if not st.session_state.df_mining_kw.empty:
            df_mining = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].assign(Source='Mining')
            df_mining.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share', 'Source']
            df_master = pd.concat([df_master, df_mining], ignore_index=True, sort=False)

        st.metric("Total de Registros Compilados", len(df_master))
        st.dataframe(df_master.fillna('N/A'))
    
    with tab4:
        st.header("Información de Listings")
        with st.container(border=True):
            st.subheader("ASINs de Cliente")
            for index, row in st.session_state.df_asin.iterrows():
                with st.expander(f"ASIN: {row['ASIN']}"):
                    st.write(f"**Marketplace:** {row['Marketplace']}")
                    st.write(f"**Título:** {row['Product Title']}")
                    st.write(f"**Bullet Points:** {row['Bullet Points']}")
                    st.write(f"**Descripción:** {row['Description'] if pd.notna(row['Description']) and str(row['Description']).strip() else 'Contenido A+'}")

            st.subheader("ASINs de Competidores")
            df_comp_asins_raw = pd.read_excel(archivo, sheet_name="CompKW", header=None)
            asin_raw = str(df_comp_asins_raw.iloc[0, 0])
            start_index = asin_raw.find('B0')
            clean_string_block = asin_raw[start_index:] if start_index != -1 else ""
            clean_asin_list = [asin.split('-')[0].strip() for asin in clean_string_block.split(',') if 'B0' in asin]
            st.dataframe(pd.DataFrame({"ASIN Competidor": clean_asin_list}))