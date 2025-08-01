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
        # Pestañas requeridas
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW")
        st.session_state.df_comp = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None)
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", skiprows=2)
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

def mostrar_histogramas(df):
    """Muestra histogramas para las métricas clave del dataframe filtrado."""
    st.subheader("Distribución de Métricas Normalizadas")

    metric_map = {
        'Norm_SV': 'Search Volume',
        'Norm_CS_Cliente': 'Click Share (Cliente)',
        'Norm_Rank_Depth': 'Rank Depth',
        'Norm_TCS': 'Total Click Share',
        'Norm_Relevance': 'Relevance'
    }
    
    col_keys = list(metric_map.keys())
    
    for i in range(0, len(col_keys), 2):
        cols = st.columns(2)
        if i < len(col_keys):
            metric_col = col_keys[i]
            with cols[0]:
                display_name = metric_map[metric_col]
                st.markdown(f"###### {display_name}")
                data_series = df[metric_col].dropna()
                if not data_series.empty:
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.hist(data_series, bins=20, edgecolor='black', range=(0,1))
                    ax.set_xlabel("Valor Normalizado (0 a 1)")
                    ax.set_ylabel('Frecuencia')
                    st.pyplot(fig)
        
        if i + 1 < len(col_keys):
            metric_col = col_keys[i+1]
            with cols[1]:
                display_name = metric_map[metric_col]
                st.markdown(f"###### {display_name}")
                data_series = df[metric_col].dropna()
                if not data_series.empty:
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.hist(data_series, bins=20, edgecolor='black', range=(0,1))
                    ax.set_xlabel("Valor Normalizado (0 a 1)")
                    ax.set_ylabel('Frecuencia')
                    st.pyplot(fig)

# --- Lógica Principal de la App ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    
    with st.expander("Análisis de Volumen de Búsqueda", expanded=True):
        st.subheader("Tabla Maestra de Keywords y Volumen de Búsqueda")

        # Preparar todas las fuentes de datos
        df_cust_sv = st.session_state.df_kw.iloc[:, [0, 15]].copy()
        df_cust_sv.columns = ['Keyword', 'Volumen Cliente']
        
        df_comp_sv = st.session_state.df_comp_data.iloc[:, [0, 8]].copy()
        df_comp_sv.columns = ['Keyword', 'Volumen Competidor']
        
        df_mining_sv = st.session_state.df_mining_kw.iloc[:, [0, 5]].copy()
        df_mining_sv.columns = ['Keyword', 'Volumen Mining']
        
        df_cust_cs = st.session_state.df_kw.iloc[:, [0, 1]].copy()
        df_cust_cs.columns = ['Keyword', 'Click Share (Cliente)']
        
        df_rev_asin = st.session_state.df_comp_data.iloc[:, [0, 5, 18]].copy()
        df_rev_asin.columns = ['Keyword', 'Rank Depth', 'Total Click Share']
        
        df_mining_rel = st.session_state.df_mining_kw.iloc[:, [0, 2]].copy()
        df_mining_rel.columns = ['Keyword', 'Relevance']

        # Unir todas las tablas
        merged1 = pd.merge(df_cust_sv, df_comp_sv, on='Keyword', how='outer')
        merged2 = pd.merge(merged1, df_mining_sv, on='Keyword', how='outer')
        merged3 = pd.merge(merged2, df_cust_cs, on='Keyword', how='left')
        merged4 = pd.merge(merged3, df_rev_asin, on='Keyword', how='left')
        final_df = pd.merge(merged4, df_mining_rel, on='Keyword', how='left')
        
        final_df['FODA'] = ''

        # Limpiar y crear columnas numéricas para cálculos
        sv_cols = ['Volumen Cliente', 'Volumen Competidor', 'Volumen Mining']
        for col in sv_cols:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0).astype(int)
        final_df['Search Volume'] = final_df[sv_cols].max(axis=1)
        
        final_df['CS_Cliente_Num'] = pd.to_numeric(final_df['Click Share (Cliente)'], errors='coerce') * 100
        final_df['Rank_Depth_Num'] = pd.to_numeric(final_df['Rank Depth'], errors='coerce')
        final_df['TCS_Num'] = pd.to_numeric(final_df['Total Click Share'], errors='coerce') * 100
        final_df['Relevance_Num'] = pd.to_numeric(final_df['Relevance'], errors='coerce')
        
        # Calcular columnas normalizadas para las gráficas
        metrics_to_normalize = {
            'Search Volume': 'Norm_SV',
            'CS_Cliente_Num': 'Norm_CS_Cliente',
            'Rank_Depth_Num': 'Norm_Rank_Depth',
            'TCS_Num': 'Norm_TCS',
            'Relevance_Num': 'Norm_Relevance'
        }
        for metric, norm_col in metrics_to_normalize.items():
            max_val = final_df[metric].max()
            if max_val > 0:
                final_df[norm_col] = final_df[metric] / max_val
            else:
                final_df[norm_col] = 0.0
        
        # UI y Lógica para FODA
        st.subheader("Definir Criterios para FODA: Fortaleza Alta")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: umbral_sv = st.number_input("Search Volume ≥", value=1000)
        with c2: umbral_cs_cliente = st.number_input("Click Share Cliente (%) ≥", value=10.0, step=0.1)
        with c3: umbral_rank_depth = st.number_input("Rank Depth ≤", value=15)
        with c4: umbral_tcs = st.number_input("Total Click Share (%) ≥", value=10.0, step=0.1)
        with c5: umbral_relevance = st.number_input("Relevance ≥", value=8)

        mask_fortaleza = (
            (final_df['Search Volume'] >= umbral_sv) &
            (final_df['CS_Cliente_Num'] >= umbral_cs_cliente) &
            (final_df['Rank_Depth_Num'] <= umbral_rank_depth) &
            (final_df['TCS_Num'] >= umbral_tcs) &
            (final_df['Relevance_Num'] >= umbral_relevance)
        )
        final_df.loc[mask_fortaleza, 'FODA'] = 'Fortaleza Alta'

        # Formatear columnas para visualización
        final_df['Click Share (Cliente)'] = pd.to_numeric(final_df['Click Share (Cliente)'], errors='coerce')
        mask = final_df['Click Share (Cliente)'].notna()
        final_df.loc[mask, 'Click Share (Cliente)'] = (final_df.loc[mask, 'Click Share (Cliente)'] * 100).round(2).astype(str) + '%'
        final_df['Click Share (Cliente)'].fillna("N/A", inplace=True)
        
        final_df['Rank Depth'] = pd.to_numeric(final_df['Rank Depth'], errors='coerce')
        mask = final_df['Rank Depth'].notna()
        final_df.loc[mask, 'Rank Depth'] = final_df.loc[mask, 'Rank Depth'].astype(int).astype(str)
        final_df['Rank Depth'].fillna("N/A", inplace=True)
        
        final_df['Total Click Share'] = pd.to_numeric(final_df['Total Click Share'], errors='coerce')
        mask = final_df['Total Click Share'].notna()
        final_df.loc[mask, 'Total Click Share'] = (final_df.loc[mask, 'Total Click Share'] * 100).round(2).astype(str) + '%'
        final_df['Total Click Share'].fillna("N/A", inplace=True)
        
        final_df['Relevance'] = pd.to_numeric(final_df['Relevance'], errors='coerce')
        mask = final_df['Relevance'].notna()
        final_df.loc[mask, 'Relevance'] = final_df.loc[mask, 'Relevance'].astype(int).astype(str)
        final_df['Relevance'].fillna("N/A", inplace=True)

        # Filtros y tabla final
        f_col, m_col = st.columns([1, 2])
        with f_col:
            opciones_volumen = ['Mostrar Todos', 'No mostrar Ceros', 'Mostrar Solo Ceros', '>= 300', '>= 500', '>= 700', '>= 1000']
            seleccion_volumen = st.selectbox("Filtrar por volumen:", opciones_volumen)
            
        df_filtrado_vol = final_df.copy()
        if seleccion_volumen == 'No mostrar Ceros':
            df_filtrado_vol = final_df[final_df['Search Volume'] > 0]
        elif seleccion_volumen == 'Mostrar Solo Ceros':
            df_filtrado_vol = final_df[final_df['Search Volume'] == 0]
        elif seleccion_volumen != 'Mostrar Todos':
            umbral = int(seleccion_volumen.replace('>= ', ''))
            df_filtrado_vol = final_df[final_df['Search Volume'] >= umbral]
        
        with m_col:
            st.metric("Registros Encontrados", len(df_filtrado_vol))
            
        columnas_finales = ['Keyword', 'Search Volume', 'Click Share (Cliente)', 'Rank Depth', 'Total Click Share', 'Relevance', 'FODA']
        result_df = df_filtrado_vol[columnas_finales]
        result_df.columns = ['Search Terms', 'Search Volume', 'Click Share (Cliente)', 'Rank Depth', 'Total Click Share', 'Relevance', 'FODA']
        
        st.dataframe(result_df.reset_index(drop=True))

        st.divider()
        st.subheader("Tabla Maestra Estadistica Descriptiva")
        
        numeric_data_for_stats = df_filtrado_vol
        
        metric_names_stats = {
            'Search Volume': 'Search Volume',
            'CS_Cliente_Num': 'Click Share (Cliente) (%)',
            'Rank_Depth_Num': 'Rank Depth',
            'TCS_Num': 'Total Click Share (%)',
            'Relevance_Num': 'Relevance'
        }
        for metric, name in metric_names_stats.items():
            st.markdown(f"**{name}**")
            data_series = numeric_data_for_stats[metric].dropna()
            
            if not data_series.empty and pd.api.types.is_numeric_dtype(data_series):
                mean_val = data_series.mean()
                median_val = data_series.median()
                mode_val_series = data_series.mode()
                display_mode = str(mode_val_series.iloc[0]) if not mode_val_series.empty else "N/A"
                std_val = data_series.std()
                skew_val = data_series.skew()
                p75_val = data_series.quantile(0.75)
                p40_val = data_series.quantile(0.40)
                cv_val = (std_val / mean_val) if mean_val > 0 else 0
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Media", f"{mean_val:,.2f}")
                c2.metric("Mediana", f"{median_val:,.2f}")
                c3.metric("Moda", display_mode)
                c4.metric("Desv. Estándar", f"{std_val:,.2f}")

                c5, c6, c7, c8 = st.columns(4)
                c5.metric("P75", f"{p75_val:,.2f}")
                c6.metric("P40", f"{p40_val:,.2f}")
                c7.metric("Asimetría", f"{skew_val:,.2f}")
                c8.metric("Coef. Variación", f"{cv_val:.2%}")
            st.divider()
        
        mostrar_histogramas(numeric_data_for_stats)


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
            
            st.divider()

            st.subheader("Terminos de Busqueda")
            opciones_clicks = {"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025}
            seleccion_clicks = st.selectbox("Filtrar por porcentaje de clics:", list(opciones_clicks.keys()))
            umbral_clicks = opciones_clicks[seleccion_clicks]
            
            df_kw_proc = st.session_state.df_kw.iloc[:, [0, 1, 15]].copy()
            df_kw_proc.columns = ["Search Terms", "Click Share", "Search Volume"]

            df_kw_proc["Click Share"] = pd.to_numeric(df_kw_proc["Click Share"], errors="coerce")
            df_kw_filtrado = df_kw_proc[df_kw_proc["Click Share"].fillna(0) > umbral_clicks].copy()
            df_kw_filtrado["Click Share"] = (df_kw_filtrado["Click Share"] * 100).round(2).astype(str) + "%"
            df_kw_filtrado["Search Volume"] = pd.to_numeric(df_kw_filtrado["Search Volume"], errors="coerce").fillna(0).astype(int)
            
            with st.expander("Ver/Ocultar Terminos de Busqueda del Cliente", expanded=True):
                st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
                st.dataframe(df_kw_filtrado.reset_index(drop=True).style.set_properties(**{"white-space": "normal", "word-wrap": "break-word"}))
                st.markdown("</div>", unsafe_allow_html=True)

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
                st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
                st.dataframe(df_asin_comp.style.set_properties(**{"white-space": "normal", "word-wrap": "break-word"}))
                st.markdown("</div>", unsafe_allow_html=True)

            st.subheader("Reverse ASIN")
            rango = st.selectbox("Mostrar terminos con ranking mayor a:", [4, 5, 6], index=1)
            df_comp_data_proc = st.session_state.df_comp_data.iloc[:, [0, 5, 8, 18]].copy()
            df_comp_data_proc.columns = ["Search Terms", "Rank Depth", "Search Volume", "Total Click Share"]
            df_comp_data_proc = df_comp_data_proc.dropna()
            
            df_comp_data_proc['Search Volume'] = pd.to_numeric(df_comp_data_proc['Search Volume'], errors='coerce').fillna(0).astype(int)
            df_comp_data_proc['Total Click Share'] = pd.to_numeric(df_comp_data_proc['Total Click Share'], errors='coerce').fillna(0)
            df_comp_data_proc['Total Click Share'] = df_comp_data_proc['Total Click Share'].round(2).astype(str) + '%'
            df_comp_data_proc['Rank Depth'] = pd.to_numeric(df_comp_data_proc['Rank Depth'], errors='coerce')
            df_comp_data_proc = df_comp_data_proc[df_comp_data_proc["Rank Depth"].notna() & (df_comp_data_proc["Rank Depth"] > rango)]

            with st.expander("Ver/Ocultar Reverse ASIN", expanded=True):
                st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)
                st.dataframe(df_comp_data_proc.reset_index(drop=True).style.set_properties(**{"white-space": "normal", "word-wrap": "break-word"}))
                st.markdown("</div>", unsafe_allow_html=True)

        # DATOS DE MINERÍA
        if st.session_state.get('df_mining_kw') is not None and not st.session_state.df_mining_kw.empty:
            with st.expander("Minería de Datos", expanded=False):
                st.markdown(f"#### Keyword Principal: *{st.session_state.mining_title}*")
                st.divider()
                df_mining_proc = st.session_state.df_mining_kw
                
                try:
                    col_a = df_mining_proc.columns[0]
                    col_c = df_mining_proc.columns[2]
                    col_f = df_mining_proc.columns[5]
                    df_to_display = df_mining_proc[[col_a, col_f, col_c]].copy()
                    df_to_display.columns = ['Search Terms', 'Search Volume', 'Relevance']
                    st.dataframe(df_to_display)
                except (IndexError, KeyError) as e:
                    st.error(f"El formato de la pestaña 'MiningKW' no es el esperado. Error: {e}")

        # SECCIÓN DE PALABRAS ÚNICAS
        with st.expander("Palabras Únicas", expanded=True): 
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
            st.divider()

            st.subheader("Tabla Consolidada de Palabras Únicas")
            
            f_col, _ = st.columns([1, 2])
            with f_col:
                opciones_freq = [1, 2, 3, 4, 5]
                default_index_freq = opciones_freq.index(2)
                umbral_freq = st.selectbox("Mostrar si cualquier frecuencia es ≥ a:", opciones_freq, index=default_index_freq)
            
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
                header_cols[1].write("**Search Term**")
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