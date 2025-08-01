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
        # --- INICIO DE LA CORRECCIÓN ---
        # Se asegura que todas las hojas de KW se lean usando la fila 2 como encabezado (header=1)
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW", header=1)
        st.session_state.df_comp = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", header=1)
        # --- FIN DE LA CORRECCIÓN ---
        
        st.session_state.avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)

        # Carga segura de pestañas opcionales
        xls = pd.ExcelFile(archivo_subido)
        
        if 'MiningKW' in xls.sheet_names:
            title_df = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=None, nrows=1, engine='openpyxl')
            title_string = title_df.iloc[0, 0] if not title_df.empty else ""
            st.session_state.mining_title = extract_mining_title(title_string)
            
            st.session_state.df_mining_kw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=1, engine='openpyxl')
        else:
            st.session_state.df_mining_kw = pd.DataFrame()
            st.session_state.mining_title = ""
        
        if 'MiningUnique' in xls.sheet_names:
            st.session_state.df_mining_unique = pd.read_excel(archivo_subido, sheet_name="MiningUnique", header=0)
        else:
            st.session_state.df_mining_unique = pd.DataFrame()

        st.session_state.datos_cargados = True
    except Exception as e:
        st.error(f"Error al leer una de las pestañas. Asegúrate de que el archivo y las pestañas existan. Error: {e}")
        st.session_state.datos_cargados = False


def anadir_palabra_a_avoids(palabra, categoria):
    """Función para añadir una palabra a la categoría correcta en el dataframe de Avoids."""
    avoids_df = st.session_state.avoids_df
    last_idx = avoids_df[categoria].last_valid_index()
    target_idx = 0 if last_idx is None else last_idx + 1

    if target_idx >= len(avoids_df):
        new_row = pd.DataFrame([[pd.NA] * len(avoids_df.columns)], columns=avoids_df.columns)
        st.session_state.avoids_df = pd.concat([avoids_df, new_row], ignore_index=True)

    st.session_state.avoids_df.loc[target_idx, categoria] = palabra

def mostrar_pagina_categorizacion():
    """Muestra la interfaz para categorizar las palabras seleccionadas."""
    with st.container(border=True):
        st.subheader("Categorizar Palabras para Añadir a Avoids")
        st.write("Has seleccionado las siguientes palabras. Ahora, por favor, asigna una categoría a cada una.")
        
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
                
                st.success("¡Palabras añadidas a la lista de exclusión correctamente!")
                st.session_state.show_categorization_form = False
                del st.session_state.palabras_para_categorizar
                st.rerun()

        if st.button("Cancelar"):
            st.session_state.show_categorization_form = False
            del st.session_state.palabras_para_categorizar
            st.rerun()

# --- Lógica Principal de la App ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    
    with st.expander("Tabla Maestra de Datos Compilados", expanded=True):
        
        # Preparar y estandarizar cada fuente de datos
        df_cust = st.session_state.df_kw.copy()
        df_cust['Source'] = 'Cliente'
        # Estandarizar nombres de columnas clave
        df_cust.rename(columns={df_cust.columns[0]: 'Search Terms', df_cust.columns[15]: 'Search Volume'}, inplace=True)

        df_comp = st.session_state.df_comp_data.copy()
        df_comp['Source'] = 'Competencia'
        df_comp.rename(columns={df_comp.columns[0]: 'Search Terms', df_comp.columns[8]: 'Search Volume'}, inplace=True)
        
        df_mining = st.session_state.df_mining_kw.copy()
        df_mining['Source'] = 'Mining'
        df_mining.rename(columns={df_mining.columns[0]: 'Search Terms', df_mining.columns[5]: 'Search Volume'}, inplace=True)
        
        # Consolidar todas las tablas
        df_master = pd.concat([df_cust, df_comp, df_mining], ignore_index=True, sort=False)
        
        # Reordenar las columnas principales
        all_cols = df_master.columns.tolist()
        initial_cols = ['Search Terms', 'Source', 'Search Volume', 'ASIN Click Share', 'Sample Click Share', 'Niche Click Share', 'Total Click Share']
        
        existing_initial_cols = [col for col in initial_cols if col in all_cols]
        other_cols = [col for col in all_cols if col not in existing_initial_cols]
        new_order = existing_initial_cols + other_cols
        df_master = df_master[new_order]

        st.dataframe(df_master, height=300)


    with st.expander("Datos para Análisis", expanded=False):

        # DATOS DEL CLIENTE
        with st.expander("Datos del cliente", expanded=False):
            st.subheader("Listing de ASIN")
            for index, row in st.session_state.df_asin.iterrows():
                try:
                    marketplace = row.iloc[0]
                    asin = row.iloc[1]
                    titulo = row.iloc[2]
                    bullets = row.iloc[3]
                    descripcion_raw = row.iloc[4]

                    if pd.isna(descripcion_raw) or str(descripcion_raw).strip() == "":
                        descripcion = "Este ASIN tiene contenido A+"
                    else:
                        descripcion = descripcion_raw

                    with st.expander(f"ASIN: {asin}"):
                        st.markdown(f"**Marketplace:** {marketplace}")
                        st.markdown("**Titulo:**")
                        st.write(titulo)
                        st.markdown("**Bullet Points:**")
                        st.write(bullets)
                        st.markdown("**Descripción:**")
                        st.write(descripcion)
                except IndexError:
                    st.warning(f"Se omitió la fila {index+1} de la pestaña 'CustListing' por no tener el formato esperado.")
                    continue
            
            st.subheader("Reverse ASIN del Producto")
            opciones_clicks = {"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025}
            seleccion_clicks = st.selectbox("ASIN Click Share >:", list(opciones_clicks.keys()))
            umbral_clicks = opciones_clicks[seleccion_clicks]
            
            df_kw_proc = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
            df_kw_proc.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]

            df_kw_proc["ASIN Click Share"] = pd.to_numeric(df_kw_proc["ASIN Click Share"], errors='coerce')
            df_kw_filtrado = df_kw_proc[df_kw_proc["ASIN Click Share"].fillna(0) > umbral_clicks].copy()
            
            df_kw_filtrado.loc[:, "ASIN Click Share"] = (df_kw_filtrado["ASIN Click Share"] * 100).round(2).astype(str) + "%"
            df_kw_filtrado.loc[:, "Search Volume"] = pd.to_numeric(df_kw_filtrado["Search Volume"], errors='coerce').fillna(0).astype(int)
            
            tcs_numeric = pd.to_numeric(df_kw_filtrado["Total Click Share"], errors='coerce').fillna(0)
            df_kw_filtrado.loc[:, "Total Click Share"] = (tcs_numeric * 100).round(2).astype(str) + '%'
            
            column_order = ["Search Terms", "Search Volume", "ASIN Click Share", "Total Click Share"]
            df_kw_filtrado = df_kw_filtrado[column_order]
            
            with st.expander("Ver/Ocultar Reverse ASIN del Producto", expanded=True):
                st.dataframe(df_kw_filtrado.reset_index(drop=True), height=400)

        # DATOS DE COMPETIDORES
        with st.expander("Datos de competidores", expanded=False):
            st.subheader("ASIN de competidores")
            with st.expander("Ver/Ocultar ASINs de Competidores", expanded=True):
                asin_raw = str(st.session_state.df_comp.iloc[0, 0])
                start_index = asin_raw.find('B0')
                clean_string_block = asin_raw[start_index:] if start_index != -1 else asin_raw
                dirty_asin_list = clean_string_block.split(',')
                clean_asin_list = [asin.split('-')[0].strip() for asin in dirty_asin_list if asin.split('-')[0].strip()]
                df_asin_comp = pd.DataFrame({"ASIN": clean_asin_list})
                st.dataframe(df_asin_comp)

            st.subheader("Reverse ASIN Competidores")
            rango = st.selectbox("Sample Product Depth >:", [4, 5, 6], index=1)
            
            df_comp_data_proc = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
            df_comp_data_proc.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
            
            df_comp_data_proc = df_comp_data_proc.dropna(subset=["Search Terms"])
            
            df_comp_data_proc['Search Volume'] = pd.to_numeric(df_comp_data_proc['Search Volume'], errors='coerce').fillna(0).astype(int)
            df_comp_data_proc['Sample Click Share'] = pd.to_numeric(df_comp_data_proc['Sample Click Share'], errors='coerce').fillna(0)
            df_comp_data_proc['Sample Click Share'] = (df_comp_data_proc['Sample Click Share'] * 100).round(2).astype(str) + '%'
            df_comp_data_proc['Niche Click Share'] = pd.to_numeric(df_comp_data_proc['Niche Click Share'], errors='coerce').fillna(0)
            df_comp_data_proc['Niche Click Share'] = (df_comp_data_proc['Niche Click Share'] * 100).round(2).astype(str) + '%'
            df_comp_data_proc['Sample Product Depth'] = pd.to_numeric(df_comp_data_proc['Sample Product Depth'], errors='coerce')
            df_comp_data_proc = df_comp_data_proc[df_comp_data_proc["Sample Product Depth"].notna() & (df_comp_data_proc["Sample Product Depth"] > rango)]

            column_order_comp = ["Search Terms", "Search Volume", "Sample Click Share", "Niche Click Share", "Sample Product Depth"]
            df_comp_data_proc = df_comp_data_proc[column_order_comp]

            with st.expander("Ver/Ocultar Reverse ASIN Competidores", expanded=True):
                st.dataframe(df_comp_data_proc.reset_index(drop=True), height=400)

        # DATOS DE MINERÍA
        if st.session_state.get('df_mining_kw') is not None and not st.session_state.df_mining_kw.empty:
            with st.expander("Mineria de Search Terms", expanded=False):
                st.markdown(f"#### Keyword Principal: *{st.session_state.mining_title}*")
                
                opciones_rel = [30, 50]
                umbral_rel = st.selectbox("Relevance ≥:", opciones_rel)

                df_mining_proc = st.session_state.df_mining_kw
                
                try:
                    df_mining_proc['Relevance'] = pd.to_numeric(df_mining_proc[df_mining_proc.columns[2]], errors='coerce').fillna(0)
                    df_to_display = df_mining_proc[df_mining_proc['Relevance'] >= umbral_rel]

                    with st.expander("Ver/Ocultar Tabla de Minería", expanded=True):
                        st.dataframe(df_to_display)

                except Exception as e:
                    st.error(f"El formato de la pestaña 'MiningKW' no es el esperado. Error: {e}")

        # SECCIÓN DE PALABRAS ÚNICAS
        with st.expander("Palabras Únicas", expanded=False): 
            if st.session_state.get('show_categorization_form', False):
                mostrar_pagina_categorizacion()
                st.divider()

            st.subheader("Palabras en lista de exclusión ('Avoids')")
            with st.expander("Ver/Ocultar Listas de Exclusión", expanded=True):
                col1, col2, col3 = st.columns(3)
                avoids_df = st.session_state.avoids_df
                avoid_column_names = avoids_df.columns.tolist()
                
                col_map = {col1: avoid_column_names[0], col2: avoid_column_names[1], col3: avoid_column_names[2]}

                for col_widget, col_name in col_map.items():
                    with col_widget:
                        st.markdown(f"**{col_name}**")
                        for index, word in avoids_df[col_name].dropna().items():
                            st.checkbox(label=str(word), key=f"del_avoid_{col_name}_{index}")
                
                st.divider()
                if st.button("Eliminar seleccionados de la lista", key="delete_avoids"):
                    palabras_eliminadas = False
                    for col_name in avoid_column_names:
                        for index, word in avoids_df[col_name].dropna().items():
                            if st.session_state.get(f"del_avoid_{col_name}_{index}"):
                                st.session_state.avoids_df.loc[index, col_name] = pd.NA
                                palabras_eliminadas = True
                    
                    if palabras_eliminadas:
                        st.success("Palabras eliminadas correctamente.")
                        st.rerun()
                    else:
                        st.warning("No has seleccionado ninguna palabra para eliminar.")

            avoid_list = pd.concat([st.session_state.avoids_df[col] for col in st.session_state.avoids_df.columns]).dropna().unique().tolist()
            
            with st.expander("Tabla Consolidada de Palabras Únicas", expanded=True):
                f_col, _ = st.columns([1, 2])
                with f_col:
                    opciones_freq = [1, 2, 3, 4, 5]
                    default_index_freq = opciones_freq.index(2)
                    umbral_freq = st.selectbox("Frecuencia Mínima (cualquier fuente) ≥:", opciones_freq, index=default_index_freq)
                
                df_cust_u = st.session_state.df_cust_unique.iloc[:, [0, 1]].copy()
                df_cust_u.columns = ['Keyword', 'Frec. Cliente']
                df_comp_u = st.session_state.df_comp_unique.iloc[:, [0, 1]].copy()
                df_comp_u.columns = ['Keyword', 'Frec. Comp.']
                df_mining_u = st.session_state.df_mining_unique.iloc[:, [0, 1]].copy()
                df_mining_u.columns = ['Keyword', 'Frec. Mining']

                merged_df_u = pd.merge(df_cust_u, df_comp_u, on='Keyword', how='outer')
                final_df_u = pd.merge(merged_df_u, df_mining_u, on='Keyword', how='outer') if not df_mining_u.empty else merged_df_u.assign(**{'Frec. Mining': 0})
                
                freq_cols = ['Frec. Cliente', 'Frec. Comp.', 'Frec. Mining']
                for col in freq_cols:
                    if col in final_df_u.columns:
                        final_df_u[col] = pd.to_numeric(final_df_u[col], errors='coerce').fillna(0).astype(int)

                df_filtered_u = final_df_u[~final_df_u['Keyword'].isin(avoid_list)]
                df_filtered_u = df_filtered_u[df_filtered_u[freq_cols].ge(umbral_freq).any(axis=1)]
                
                if not df_filtered_u.empty:
                    header_cols_spec = [0.5, 2, 1, 1, 1]
                    header_cols = st.columns(header_cols_spec)
                    header_cols[0].write("**Sel.**")
                    header_cols[1].write("**Keyword**")
                    header_cols[2].write("**Frec. Cliente**")
                    header_cols[3].write("**Frec. Comp.**")
                    header_cols[4].write("**Frec. Mining**")
                    st.divider()

                    for index, row in df_filtered_u.iterrows():
                        row_cols = st.columns(header_cols_spec)
                        row_cols[0].checkbox("", key=f"consolidada_cb_{index}")
                        row_cols[1].write(row['Keyword'])
                        row_cols[2].write(str(row['Frec. Cliente']))
                        row_cols[3].write(str(row['Frec. Comp.']))
                        row_cols[4].write(str(row['Frec. Mining']))

                    st.divider()

                    if st.button("añadir a Avoids", key="consolidada_add_to_avoids"):
                        palabras_a_anadir = [row['Keyword'] for index, row in df_filtered_u.iterrows() if st.session_state.get(f"consolidada_cb_{index}")]
                        if palabras_a_anadir:
                            st.session_state.palabras_para_categorizar = palabras_a_anadir
                            st.session_state.show_categorization_form = True
                            st.rerun()
                        else:
                            st.warning("No has seleccionado ninguna palabra.")
                else:
                    st.write("No hay palabras únicas para mostrar con los filtros actuales.")