import streamlit as st
import pandas as pd
import re

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
        
        # Calcular Z-Scores
        metrics_to_zscore = {
            'Search Volume': 'Z-Score SV',
            'CS_Cliente_Num': 'Z-Score CS Cliente',
            'Rank_Depth_Num': 'Z-Score Rank Depth',
            'TCS_Num': 'Z-Score TCS',
            'Relevance_Num': 'Z-Score Relevance'
        }
        for metric, z_col in metrics_to_zscore.items():
            mean = final_df[metric].mean()
            std = final_df[metric].std()
            if std > 0:
                final_df[z_col] = ((final_df[metric] - mean) / std).round(2)
            else:
                final_df[z_col] = 0.0
        
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
            
        columnas_finales = ['Keyword', 'Search Volume', 'Click Share (Cliente)', 'Rank Depth', 'Total Click Share', 'Relevance', 'FODA'] + list(metrics_to_zscore.values())
        result_df = df_filtrado_vol[columnas_finales]
        result_df.columns = ['Search Terms', 'Search Volume', 'Click Share (Cliente)', 'Rank Depth', 'Total Click Share', 'Relevance', 'FODA'] + list(metrics_to_zscore.values())
        
        st.dataframe(result_df.reset_index(drop=True))

        st.divider()
        st.subheader("Tabla Maestra Estadistica Descriptiva")
        
        numeric_data_for_stats = df_filtrado_vol
        
        metric_names = {
            'Search Volume': 'Search Volume',
            'CS_Cliente_Num': 'Click Share (Cliente) (%)',
            'Rank_Depth_Num': 'Rank Depth',
            'TCS_Num': 'Total Click Share (%)',
            'Relevance_Num': 'Relevance'
        }
        for metric, name in metric_names.items():
            st.markdown(f"**{name}**")
            data_series = numeric_data_for_stats[metric].dropna()
            
            if not data_series.empty and pd.api.types.is_numeric_dtype(data_series):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Media", f"{data_series.mean():,.2f}")
                c2.metric("Mediana", f"{data_series.median():,.2f}")
                c3.metric("Asimetría", f"{data_series.skew():,.2f}")
                c4.metric("Desv. Estándar", f"{data_series.std():,.2f}")

                c5, c6, c7, c8 = st.columns(4)
                c5.metric("P75", f"{data_series.quantile(0.75):,.2f}")
                c6.metric("P40", f"{data_series.quantile(0.40):,.2f}")
                
                mode_val = data_series.mode()
                display_mode = str(mode_val.iloc[0]) if not mode_val.empty else "N/A"
                c7.metric("Moda", display_mode)
                
                mean_val = data_series.mean()
                std_val = data_series.std()
                cv_val = (std_val / mean_val) if mean_val > 0 else 0
                c8.metric("Coef. Variación", f"{cv_val:.2%}")
            st.divider()


    with st.expander("Datos para Análisis", expanded=False):
        # ... (código completo y restaurado de las secciones de datos)