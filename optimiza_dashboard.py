{\rtf1\ansi\ansicpg1252\cocoartf2706
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
\
st.set_page_config(page_title="Optimizaci\'f3n de Listado", layout="wide")\
\
\
# --- Funciones ---\
def inicializar_datos(archivo_subido):\
    """Carga los datos del Excel y los guarda en el session_state."""\
    try:\
        st.session_state.df_asin = pd.read_excel(archivo_subido, sheet_name="CustListing")\
        st.session_state.df_kw = pd.read_excel(archivo_subido, sheet_name="CustKW")\
        st.session_state.df_comp = pd.read_excel(archivo_subido, sheet_name="CompKW", header=None)\
        st.session_state.df_comp_data = pd.read_excel(archivo_subido, sheet_name="CompKW", skiprows=2)\
        st.session_state.avoids_df = pd.read_excel(archivo_subido, sheet_name="Avoids", header=0)\
        st.session_state.df_cust_unique = pd.read_excel(archivo_subido, sheet_name="CustUnique", header=0)\
        st.session_state.df_comp_unique = pd.read_excel(archivo_subido, sheet_name="CompUnique", header=0)\
        st.session_state.df_mining_kw = pd.read_excel(archivo_subido, sheet_name="MiningKW", header=0)\
        st.session_state.df_mining_unique = pd.read_excel(archivo_subido, sheet_name="MiningUnique", header=0)\
\
        st.session_state.datos_cargados = True\
    except Exception as e:\
        st.error(f"No se pudo leer el archivo: \{e\}")\
        st.session_state.datos_cargados = False\
\
def anadir_palabra_a_avoids(palabra, categoria):\
    """Funci\'f3n para a\'f1adir una palabra a la categor\'eda correcta en el dataframe de Avoids."""\
    avoids_df = st.session_state.avoids_df\
    last_idx = avoids_df[categoria].last_valid_index()\
    target_idx = 0 if last_idx is None else last_idx + 1\
\
    if target_idx >= len(avoids_df):\
        new_row = pd.DataFrame([[pd.NA] * len(avoids_df.columns)], columns=avoids_df.columns)\
        st.session_state.avoids_df = pd.concat([avoids_df, new_row], ignore_index=True)\
\
    st.session_state.avoids_df.loc[target_idx, categoria] = palabra\
\
def mostrar_pagina_categorizacion():\
    """Muestra la interfaz para categorizar las palabras seleccionadas."""\
    with st.container(border=True):\
        st.subheader("Categorizar Palabras para A\'f1adir a Avoids")\
        st.write("Has seleccionado las siguientes palabras. Ahora, por favor, asigna una categor\'eda a cada una.")\
        \
        palabras = st.session_state.get('palabras_para_categorizar', [])\
        \
        if not palabras:\
            st.session_state.show_categorization_form = False\
            st.rerun()\
            return\
\
        avoid_column_names = st.session_state.avoids_df.columns.tolist()\
\
        with st.form("form_categorizacion"):\
            for palabra in palabras:\
                cols = st.columns([2, 3])\
                cols[0].write(f"**\{palabra\}**")\
                cols[1].selectbox("Categor\'eda", avoid_column_names, key=f"cat_\{palabra\}", label_visibility="collapsed")\
            \
            submitted = st.form_submit_button("Confirmar y A\'f1adir Palabras")\
            if submitted:\
                for palabra in palabras:\
                    categoria = st.session_state[f"cat_\{palabra\}"]\
                    anadir_palabra_a_avoids(palabra, categoria)\
                \
                st.success("\'a1Palabras a\'f1adidas a la lista de exclusi\'f3n correctamente!")\
                st.session_state.show_categorization_form = False\
                del st.session_state.palabras_para_categorizar\
                st.rerun()\
\
        if st.button("Cancelar"):\
            st.session_state.show_categorization_form = False\
            del st.session_state.palabras_para_categorizar\
            st.rerun()\
\
# --- L\'f3gica Principal de la App ---\
st.title("Optimizaci\'f3n de Listado - Dashboard")\
archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])\
\
if archivo:\
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != archivo.name:\
        st.session_state.clear()\
        st.session_state.last_uploaded_file = archivo.name\
        inicializar_datos(archivo)\
\
if st.session_state.get('datos_cargados', False):\
    \
    # DATOS DEL CLIENTE\
    with st.expander("Datos del cliente", expanded=False):\
        subtabs = st.radio("Selecciona una vista:", ["Listado de ASINs", "Palabras Clave (Keywords)"], key="cliente_radio")\
        if subtabs == "Listado de ASINs":\
            for _, row in st.session_state.df_asin.iterrows():\
                asin = row.get("ASIN", "")\
                titulo = row.get("Product Title", "")\
                bullets = row.get("Bullet Points", "")\
                descripcion = row.get("Description", "")\
                with st.expander(f"ASIN: \{asin\}"):\
                    st.markdown("**T\'edtulo del producto:**")\
                    st.write(titulo)\
                    st.markdown("**Puntos clave:**")\
                    st.write(bullets)\
                    if pd.notna(descripcion) and str(descripcion).strip():\
                        st.markdown("**Descripci\'f3n:**")\
                        st.write(descripcion)\
        elif subtabs == "Palabras Clave (Keywords)":\
            opciones = \{"Mayor al 5%": 0.05, "Mayor al 2.5%": 0.025\}\
            seleccion = st.selectbox("Filtrar por porcentaje de clics:", list(opciones.keys()))\
            umbral = opciones[seleccion]\
            \
            # --- INICIO DE LA CORRECCI\'d3N ---\
            # Se leen las columnas por su posici\'f3n (A=0, B=1, P=15)\
            df_kw_copy = st.session_state.df_kw.iloc[:, [0, 1, 15]].copy()\
            # Se renombran las columnas para que el resto del c\'f3digo funcione\
            df_kw_copy.columns = ["Keyword", "Click Share", "M. Searches"]\
            # --- FIN DE LA CORRECCI\'d3N ---\
\
            df_kw_copy["Click Share"] = pd.to_numeric(df_kw_copy["Click Share"], errors="coerce")\
            df_kw_filtrado = df_kw_copy[df_kw_copy["Click Share"].fillna(0) > umbral]\
            df_kw_filtrado["Click Share"] = (df_kw_filtrado["Click Share"] * 100).round(2).astype(str) + "%"\
            df_kw_filtrado["M. Searches"] = pd.to_numeric(df_kw_filtrado["M. Searches"], errors="coerce").fillna(0).astype(int)\
            \
            # La variable 'columnas' ahora se basa en los nuevos nombres estandarizados\
            columnas_a_mostrar = ["Keyword", "M. Searches", "Click Share"]\
            \
            with st.expander("Ver/Ocultar Keywords del Cliente", expanded=True):\
                st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)\
                st.dataframe(df_kw_filtrado[columnas_a_mostrar].reset_index(drop=True).style.set_properties(**\{"white-space": "normal", "word-wrap": "break-word"\}))\
                st.markdown("</div>", unsafe_allow_html=True)\
\
    # DATOS DE COMPETIDORES\
    with st.expander("Datos de competidores", expanded=False):\
        st.subheader("ASIN de competidores")\
        with st.expander("Ver/Ocultar ASINs de Competidores", expanded=True):\
            asin_raw = str(st.session_state.df_comp.iloc[0, 0])\
            if "ExpandKeywords" in asin_raw:\
                cuerpo = asin_raw.replace("ExpandKeywords(439)-US-", "").split("-Last-30-days")[0]\
                asin_list = [a.strip() for a in cuerpo.split(",") if a.strip()]\
                df_asin_comp = pd.DataFrame(\{"ASIN de competidor": asin_list\})\
                st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)\
                st.dataframe(df_asin_comp.style.set_properties(**\{"white-space": "normal", "word-wrap": "break-word"\}))\
                st.markdown("</div>", unsafe_allow_html=True)\
        st.subheader("Keywords por ranking de competidor")\
        rango = st.selectbox("Mostrar keywords con ranking mayor a:", [4, 5, 6], index=1)\
        df_comp_data_copy = st.session_state.df_comp_data.copy()\
        df_comp_data_copy.replace(r'^\\s*$', pd.NA, regex=True, inplace=True)\
        cols = df_comp_data_copy.iloc[:, [0, 5, 8, 18]].copy()\
        cols.columns = ["Palabra clave", "Ranking ASIN", "Impresiones", "CTR"]\
        cols = cols.dropna()\
        cols['Impresiones'] = pd.to_numeric(cols['Impresiones'], errors='coerce').fillna(0).astype(int)\
        cols['CTR'] = pd.to_numeric(cols['CTR'], errors='coerce').fillna(0)\
        cols['CTR'] = cols['CTR'].round(2).astype(str) + '%'\
        cols['Ranking ASIN'] = pd.to_numeric(cols['Ranking ASIN'], errors='coerce')\
        cols = cols[cols["Ranking ASIN"].notna() & (cols["Ranking ASIN"] > rango)]\
        with st.expander("Ver/Ocultar Keywords de Competidores por Ranking", expanded=True):\
            st.markdown("<div style='max-width: 800px'>", unsafe_allow_html=True)\
            st.dataframe(cols.reset_index(drop=True).style.set_properties(**\{"white-space": "normal", "word-wrap": "break-word"\}))\
            st.markdown("</div>", unsafe_allow_html=True)\
\
    # DATOS DE MINING\
    with st.expander("Datos de Mining", expanded=False):\
        avoid_column_names_mining = st.session_state.avoids_df.columns.tolist()\
        avoid_list_mining = pd.concat([st.session_state.avoids_df[col] for col in avoid_column_names_mining]).dropna().unique().tolist()\
\
        st.subheader("Palabras \'fanicas de Mining (filtradas)")\
        filtro_mining = st.checkbox("Ocultar frecuencia \uc0\u8804  2", value=True, key="fm")\
        \
        with st.expander("Ver/Ocultar Palabras de Mining", expanded=True):\
            df_mining = st.session_state.df_mining_unique\
            df_mining_filtered = df_mining[~df_mining[df_mining.columns[0]].isin(avoid_list_mining)]\
            if filtro_mining and len(df_mining.columns) > 1:\
                freq_col_mining = df_mining.columns[1]\
                df_mining_filtered.loc[:, freq_col_mining] = pd.to_numeric(df_mining_filtered[freq_col_mining], errors='coerce')\
                df_mining_filtered = df_mining_filtered[df_mining_filtered[freq_col_mining].notna() & (df_mining_filtered[freq_col_mining] > 2)]\
\
            if not df_mining_filtered.empty:\
                header_cols_spec = [0.5, 2] + [1] * (len(df_mining_filtered.columns) - 1)\
                header_cols = st.columns(header_cols_spec)\
                header_cols[0].write("**Sel.**")\
                for i, col_name in enumerate(df_mining_filtered.columns):\
                    header_cols[i+1].write(f"**\{col_name\}**")\
                st.divider()\
\
                for index, row in df_mining_filtered.iterrows():\
                    row_cols = st.columns(header_cols_spec)\
                    row_cols[0].checkbox("", key=f"mining_cb_\{index\}")\
                    for i, col_name in enumerate(df_mining_filtered.columns):\
                        row_cols[i+1].write(row[col_name])\
                \
                st.divider()\
                if st.button("a\'f1adir a Avoids", key="mining_add_to_avoids"):\
                    palabras_a_anadir = []\
                    for index, row in df_mining_filtered.iterrows():\
                        if st.session_state.get(f"mining_cb_\{index\}"):\
                            palabra = row[df_mining_filtered.columns[0]]\
                            palabras_a_anadir.append(palabra)\
                    \
                    if palabras_a_anadir:\
                        st.session_state.palabras_para_categorizar = palabras_a_anadir\
                        st.session_state.show_categorization_form = True\
                        st.rerun() \
                    else:\
                        st.warning("No has seleccionado ninguna palabra.")\
            else:\
                st.write("No hay datos de palabras \'fanicas de mining para mostrar.")\
\
    # SECCI\'d3N DE PALABRAS \'daNICAS\
    with st.expander("Palabras \'danicas", expanded=True): \
        \
        if st.session_state.get('show_categorization_form', False):\
            mostrar_pagina_categorizacion()\
            st.divider()\
\
        st.subheader("Palabras en lista de exclusi\'f3n ('Avoids')")\
        with st.expander("Ver/Ocultar Listas de Exclusi\'f3n", expanded=True):\
            col1, col2, col3 = st.columns(3)\
            avoids_df = st.session_state.avoids_df\
            avoid_column_names = avoids_df.columns.tolist()\
            \
            col_map = \{col1: avoid_column_names[0], col2: avoid_column_names[1], col3: avoid_column_names[2]\}\
\
            for col_widget, col_name in col_map.items():\
                with col_widget:\
                    st.markdown(f"**\{col_name\}**")\
                    for index, word in avoids_df[col_name].dropna().items():\
                        st.checkbox(label=str(word), key=f"del_avoid_\{col_name\}_\{index\}")\
            \
            st.divider()\
            if st.button("Eliminar seleccionados de la lista", key="delete_avoids"):\
                palabras_eliminadas = False\
                for col_name in avoid_column_names:\
                    for index, word in avoids_df[col_name].dropna().items():\
                        if st.session_state.get(f"del_avoid_\{col_name\}_\{index\}"):\
                            st.session_state.avoids_df.loc[index, col_name] = pd.NA\
                            palabras_eliminadas = True\
                \
                if palabras_eliminadas:\
                    st.success("Palabras eliminadas correctamente.")\
                    st.rerun()\
                else:\
                    st.warning("No has seleccionado ninguna palabra para eliminar.")\
\
        avoid_list = pd.concat([st.session_state.avoids_df[col] for col in avoid_column_names]).dropna().unique().tolist()\
        st.divider()\
\
        # --- PALABRAS \'daNICAS DEL CLIENTE ---\
        st.subheader("Palabras \'fanicas del cliente (filtradas)")\
        filtro_cust = st.checkbox("Ocultar frecuencia \uc0\u8804  2", value=True, key="fc")\
        \
        with st.expander("Ver/Ocultar Palabras del Cliente", expanded=True):\
            df_cust = st.session_state.df_cust_unique\
            df_cust_filtered = df_cust[~df_cust[df_cust.columns[0]].isin(avoid_list)]\
            if filtro_cust and len(df_cust.columns) > 1:\
                freq_col_cust = df_cust.columns[1]\
                df_cust_filtered.loc[:, freq_col_cust] = pd.to_numeric(df_cust_filtered[freq_col_cust], errors='coerce')\
                df_cust_filtered = df_cust_filtered[df_cust_filtered[freq_col_cust].notna() & (df_cust_filtered[freq_col_cust] > 2)]\
\
            if not df_cust_filtered.empty:\
                header_cols_spec = [0.5, 2] + [1] * (len(df_cust_filtered.columns) - 1)\
                header_cols = st.columns(header_cols_spec)\
                header_cols[0].write("**Sel.**")\
                for i, col_name in enumerate(df_cust_filtered.columns):\
                    header_cols[i+1].write(f"**\{col_name\}**")\
                st.divider()\
\
                for index, row in df_cust_filtered.iterrows():\
                    row_cols = st.columns(header_cols_spec)\
                    row_cols[0].checkbox("", key=f"cust_cb_\{index\}")\
                    for i, col_name in enumerate(df_cust_filtered.columns):\
                        row_cols[i+1].write(row[col_name])\
                \
                st.divider()\
                if st.button("a\'f1adir a Avoids", key="cust_add_to_avoids"):\
                    palabras_a_anadir = []\
                    for index, row in df_cust_filtered.iterrows():\
                        if st.session_state.get(f"cust_cb_\{index\}"):\
                            palabra = row[df_cust_filtered.columns[0]]\
                            palabras_a_anadir.append(palabra)\
                    \
                    if palabras_a_anadir:\
                        st.session_state.palabras_para_categorizar = palabras_a_anadir\
                        st.session_state.show_categorization_form = True\
                        st.rerun() \
                    else:\
                        st.warning("No has seleccionado ninguna palabra.")\
            else:\
                st.write("No hay datos de palabras \'fanicas del cliente para mostrar.")\
        \
        # --- PALABRAS \'daNICAS DE COMPETIDORES ---\
        st.subheader("Palabras \'fanicas de competidores (filtradas)")\
        filtro_comp = st.checkbox("Ocultar frecuencia \uc0\u8804  2 (competidores)", value=True, key="fc2")\
\
        with st.expander("Ver/Ocultar Palabras de Competidores", expanded=True):\
            df_comp = st.session_state.df_comp_unique\
            df_comp_filtered = df_comp[~df_comp[df_comp.columns[0]].isin(avoid_list)]\
            if filtro_comp and len(df_comp.columns) > 1:\
                freq_col_comp = df_comp.columns[1]\
                df_comp_filtered.loc[:, freq_col_comp] = pd.to_numeric(df_comp_filtered[freq_col_comp], errors='coerce')\
                df_comp_filtered = df_comp_filtered[df_comp_filtered[freq_col_comp].notna() & (df_comp_filtered[freq_col_comp] > 2)]\
\
            if not df_comp_filtered.empty:\
                header_cols_spec_comp = [0.5, 2] + [1] * (len(df_comp_filtered.columns) - 1)\
                header_cols_comp = st.columns(header_cols_spec_comp)\
                header_cols_comp[0].write("**Sel.**")\
                for i, col_name in enumerate(df_comp_filtered.columns):\
                    header_cols_comp[i+1].write(f"**\{col_name\}**")\
                st.divider()\
\
                for index, row in df_comp_filtered.iterrows():\
                    row_cols_comp = st.columns(header_cols_spec_comp)\
                    row_cols_comp[0].checkbox("", key=f"comp_cb_\{index\}")\
                    for i, col_name in enumerate(df_comp_filtered.columns):\
                        row_cols_comp[i+1].write(row[col_name])\
                \
                st.divider()\
                if st.button("a\'f1adir a Avoids", key="comp_add_to_avoids"):\
                    palabras_a_anadir_comp = []\
                    for index, row in df_comp_filtered.iterrows():\
                        if st.session_state.get(f"comp_cb_\{index\}"):\
                            palabra = row[df_comp_filtered.columns[0]]\
                            palabras_a_anadir_comp.append(palabra)\
                            \
                    if palabras_a_anadir_comp:\
                        st.session_state.palabras_para_categorizar = palabras_a_anadir_comp\
                        st.session_state.show_categorization_form = True\
                        st.rerun() \
                    else:\
                        st.warning("No has seleccionado ninguna palabra.")\
            else:\
                st.write("No hay datos de palabras \'fanicas de competidores para mostrar.")}