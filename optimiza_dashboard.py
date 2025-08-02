if st.session_state.get('datos_cargados', False):
    tabs = st.tabs(["Cliente", "Competidores", "Minería", "Palabras Únicas"])

    # --- TAB CLIENTE ---
    with tabs[0]:
        st.subheader("Datos del Cliente")
        for index, row in st.session_state.df_asin.iterrows():
            try:
                asin = row.iloc[1]
                titulo = row.iloc[2]
                bullets = row.iloc[3]
                descripcion = row.iloc[4] if pd.notna(row.iloc[4]) else "Este ASIN tiene contenido A+"
                st.markdown(f"**ASIN:** {asin} | **Título:** {titulo}")
            except:
                continue

        st.subheader("Reverse ASIN del Producto")
        df_kw_proc = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
        df_kw_proc.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]
        df_kw_proc["ASIN Click Share"] = pd.to_numeric(df_kw_proc["ASIN Click Share"], errors='coerce')
        df_kw_proc["ASIN Click Share"] = (df_kw_proc["ASIN Click Share"] * 100).round(2).astype(str) + "%"
        df_kw_proc["Search Volume"] = pd.to_numeric(df_kw_proc["Search Volume"], errors='coerce').fillna(0).astype(int)
        df_kw_proc["Total Click Share"] = (pd.to_numeric(df_kw_proc["Total Click Share"], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'
        st.dataframe(df_kw_proc.reset_index(drop=True), height=400)

    # --- TAB COMPETIDORES ---
    with tabs[1]:
        st.subheader("Reverse ASIN Competidores")
        df_comp_data_proc = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
        df_comp_data_proc.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
        df_comp_data_proc = df_comp_data_proc.dropna(subset=["Search Terms"])
        df_comp_data_proc['Sample Click Share'] = (pd.to_numeric(df_comp_data_proc['Sample Click Share'], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'
        df_comp_data_proc['Niche Click Share'] = (pd.to_numeric(df_comp_data_proc['Niche Click Share'], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'
        df_comp_data_proc['Search Volume'] = pd.to_numeric(df_comp_data_proc['Search Volume'], errors='coerce').fillna(0).astype(int)
        st.dataframe(df_comp_data_proc.reset_index(drop=True), height=400)

    # --- TAB MINERÍA ---
    with tabs[2]:
        st.subheader("Minería de Search Terms")
        if not st.session_state.df_mining_kw.empty:
            df_mining_proc = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
            df_mining_proc.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']
            df_mining_proc['Niche Click Share'] = (pd.to_numeric(df_mining_proc['Niche Click Share'], errors='coerce').fillna(0) * 100).round(2).astype(str) + '%'
            st.dataframe(df_mining_proc.reset_index(drop=True), height=400)
        else:
            st.write("No hay datos de Minería disponibles.")

    # --- TAB PALABRAS ÚNICAS ---
    with tabs[3]:
        st.subheader("Palabras Únicas (Avoids)")
        # Aquí pega tu lógica de Avoids tal como la tienes en tu código actual.
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
    st.dataframe(df_master, height=600)
