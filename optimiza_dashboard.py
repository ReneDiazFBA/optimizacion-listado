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
    st.subheader("Distribución de Métricas (Escala Logarítmica)")

    metric_map = {
        'Search Volume': 'Search Volume',
        'CS_Cliente_Num': 'Click Share (Cliente)',
        'Rank_Depth_Num': 'Rank Depth',
        'TCS_Num': 'Total Click Share',
        'Relevance_Num': 'Relevance'
    }
    
    col_keys = list(metric_map.keys())
    
    for i in range(0, len(col_keys), 2):
        cols = st.columns(2)
        if i < len(col_keys):
            metric_col = col_keys[i]
            with cols[0]:
                display_name = metric_map[metric_col]
                st.markdown(f"###### {display_name}")
                data_series = df[metric_col][df[metric_col] > 0].dropna()
                if not data_series.empty:
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.hist(data_series, bins=20, edgecolor='black')
                    ax.set_xscale('log')
                    ax.set_title(f'Distribución de {display_name}')
                    ax.set_xlabel(f"{display_name} (Escala Log)")
                    ax.set_ylabel('Frecuencia')
                    st.pyplot(fig)
                else:
                    st.write(f"No hay datos positivos para graficar para {display_name}.")

        if i + 1 < len(col_keys):
            metric_col = col_keys[i+1]
            with cols[1]:
                display_name = metric_map[metric_col]
                st.markdown(f"###### {display_name}")
                data_series = df[metric_col][df[metric_col] > 0].dropna()
                if not data_series.empty:
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ax.hist(data_series, bins=20, edgecolor='black')
                    ax.set_xscale('log')
                    ax.set_title(f'Distribución de {display_name}')
                    ax.set_xlabel(f"{display_name} (Escala Log)")
                    ax.set_ylabel('Frecuencia')
                    st.pyplot(fig)
                else:
                    st.write(f"No hay datos positivos para graficar para {display_name}.")


# --- Lógica Principal de la App ---
st.title("Optimización de Listado - Dashboard")
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:
        st.session_state.clear()
        st.session_state.last_uploaded_file = archivo.name
        inicializar_datos(archivo)

if st.session_state.get('datos_cargados', False):
    
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
            
            df_kw_proc = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
            df_kw_proc.columns = ["Search Terms", "Click Share", "Search Volume", "Total Click Share"]

            df_kw_proc["Click Share"] = pd.to_numeric(df_kw_proc["Click Share"], errors='coerce')
            df_kw_filtrado = df_kw_proc[df_kw_proc["Click Share"].fillna(0) > umbral_clicks].copy()
            
            df_kw_filtrado.loc[:, "Click Share"] = (df_kw_filtrado["Click Share"] * 100).round(2).astype(str) + "%"
            df_kw_filtrado.loc[:, "Search Volume"] = pd.to_numeric(df_kw_filtrado["Search Volume"], errors='coerce').fillna(0).astype(int)
            
            df_kw_filtrado.loc[:, "Total Click Share"] = pd.to_numeric(df_kw_filtrado["Total Click Share"], errors='coerce').fillna(0)
            df_kw_filtrado.loc[:, "Total Click Share"] = (df_kw_filtrado["Total Click Share"] * 100).round(2).astype(str) + '%'
            
            with st.expander("Ver/Ocultar Terminos de Busqueda del Cliente", expanded=True):
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

            st.subheader("Reverse ASIN")
            rango = st.selectbox("Mostrar terminos con ranking mayor a:", [4, 5, 6], index=1)
            
            # --- INICIO DE LA CORRECCIÓN ---
            df_comp_data_proc = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
            df_comp_data_proc.columns = ["Search Terms", "Click Share", "Rank Depth", "Search Volume", "Total Click Share"]
            # --- FIN DE LA CORRECCIÓN ---
            
            df_comp_data_proc = df_comp_data_proc.dropna(subset=["Search Terms"])
            
            df_comp_data_proc['Search Volume'] = pd.to_numeric(df_comp_data_proc['Search Volume'], errors='coerce').fillna(0).astype(int)
            df_comp_data_proc['Click Share'] = pd.to_numeric(df_comp_data_proc['Click Share'], errors='coerce').fillna(0)
            df_comp_data_proc['Click Share'] = (df_comp_data_proc['Click Share'] * 100).round(2).astype(str) + '%'
            df_comp_data_proc['Total Click Share'] = pd.to_numeric(df_comp_data_proc['Total Click Share'], errors='coerce').fillna(0)
            df_comp_data_proc['Total Click Share'] = (df_comp_data_proc['Total Click Share'] * 100).round(2).astype(str) + '%'
            df_comp_data_proc['Rank Depth'] = pd.to_numeric(df_comp_data_proc['Rank Depth'], errors='coerce')
            df_comp_data_proc = df_comp_data_proc[df_comp_data_proc["Rank Depth"].notna() & (df_comp_data_proc["Rank Depth"] > rango)]

            with st.expander("Ver/Ocultar Reverse ASIN", expanded=True):
                st.dataframe(df_comp_data_proc.reset_index(drop=True), height=400)

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
        with st.expander("Palabras Únicas", expanded=False): 
            # ... (código sin cambios)
    
    with st.expander("Análisis de Volumen de Búsqueda", expanded=True):
        # ... (código sin cambios)