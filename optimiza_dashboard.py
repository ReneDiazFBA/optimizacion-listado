# --- Sección Tabla Maestra Corregida (único cambio hecho) ---
    with st.expander("Tabla Maestra de Datos Compilados", expanded=True):

        # --- Prepara tabla Cliente ---
        df_cust = st.session_state.df_kw.iloc[:, [0, 1, 15, 25]].copy()
        df_cust.columns = ["Search Terms", "ASIN Click Share", "Search Volume", "Total Click Share"]
        df_cust['Source'] = 'Cliente'
        df_cust = df_cust[pd.to_numeric(df_cust["Search Volume"], errors='coerce').notna()]  # Limpia headers colados

        # --- Prepara tabla Competencia ---
        df_comp = st.session_state.df_comp_data.iloc[:, [0, 2, 5, 8, 18]].copy()
        df_comp.columns = ["Search Terms", "Sample Click Share", "Sample Product Depth", "Search Volume", "Niche Click Share"]
        df_comp['Source'] = 'Competencia'
        df_comp = df_comp[pd.to_numeric(df_comp["Search Volume"], errors='coerce').notna()]  # Limpia headers colados

        # --- Prepara tabla Mining ---
        df_mining = st.session_state.df_mining_kw.iloc[:, [0, 2, 5, 12, 15]].copy()
        df_mining.columns = ['Search Terms', 'Relevance', 'Search Volume', 'Niche Product Depth', 'Niche Click Share']
        df_mining['Source'] = 'Mining'
        df_mining = df_mining[pd.to_numeric(df_mining["Search Volume"], errors='coerce').notna()]  # Limpia headers colados

        # --- Consolidación ---
        df_master = pd.concat([df_cust, df_comp, df_mining], ignore_index=True, sort=False)

        # --- Formateo de columnas numéricas ---
        numeric_cols = ['Search Volume', 'ASIN Click Share', 'Total Click Share', 'Sample Click Share', 'Niche Click Share', 'Sample Product Depth', 'Niche Product Depth', 'Relevance']
        for col in numeric_cols:
            if col in df_master.columns:
                df_master[col] = pd.to_numeric(df_master[col], errors='coerce')

        percent_cols = ['ASIN Click Share', 'Total Click Share', 'Sample Click Share', 'Niche Click Share']
        for col in percent_cols:
            if col in df_master.columns:
                mask = df_master[col].notna()
                df_master.loc[mask, col] = (df_master.loc[mask, col] * 100).round(2).astype(str) + '%'

        # --- Reordenar columnas ---
        column_order = [
            'Search Terms', 'Source', 'Search Volume',
            'ASIN Click Share', 'Sample Click Share', 'Niche Click Share', 'Total Click Share',
            'Sample Product Depth', 'Niche Product Depth', 'Relevance'
        ]
        existing_cols = [col for col in column_order if col in df_master.columns]
        df_master = df_master[existing_cols].fillna('N/A')

        st.metric("Total de Registros Compilados", len(df_master))
        st.dataframe(df_master, height=300)
