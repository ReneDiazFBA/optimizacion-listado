import pandas as pd

# Leer las hojas comenzando desde la fila 3 (skiprows=2)
custkw = pd.read_excel("tu_archivo.xlsx", sheet_name="CustKW", skiprows=2)
compkw = pd.read_excel("tu_archivo.xlsx", sheet_name="CompKW", skiprows=2)
miningkw = pd.read_excel("tu_archivo.xlsx", sheet_name="MiningKW", skiprows=2)

# Renombrar columnas para estandarizar nombres
custkw.rename(columns={
    'Keyword Phrase': 'Keyword',
    'Monthly Searches': 'Search Volume',
    'Click Share': 'Click Share (Client)'
}, inplace=True)

compkw.rename(columns={
    'Keyword': 'Keyword',
    'Searched / Month': 'Search Volume',
    'Click Share': 'Click Share (Sample)',
    'Total Click Share': 'Click Share (Niche)',
    'Products': 'Sample Product Depth'
}, inplace=True)

miningkw.rename(columns={
    'Keyword': 'Keyword',
    'Monthly Searches': 'Search Volume',
    'Total Click Share': 'Click Share (Niche)',
    'Products': 'Niche Product Depth',
    'Relevancy': 'Relevancy'
}, inplace=True)

# Crear lista única de Keywords desde las 3 fuentes
all_keywords = pd.Series(pd.concat([custkw['Keyword'], compkw['Keyword'], miningkw['Keyword']])).dropna().unique()

# Crear DataFrame consolidado con las Keywords (desde fila 3)
merged_df = pd.DataFrame({'Keyword': all_keywords})

# Hacer LEFT JOIN con cada tabla fuente para traer sus datos específicos
merged_df = merged_df.merge(custkw[['Keyword', 'Search Volume', 'Click Share (Client)']], on='Keyword', how='left')
merged_df = merged_df.merge(compkw[['Keyword', 'Click Share (Sample)', 'Click Share (Niche)', 'Sample Product Depth']], on='Keyword', how='left')
merged_df = merged_df.merge(miningkw[['Keyword', 'Click Share (Niche)', 'Niche Product Depth', 'Relevancy']], on='Keyword', how='left', suffixes=('', ' (Mining)'))

# Si existe duplicación de columna Click Share (Niche), fusionarlas en una sola
if 'Click Share (Niche) (Mining)' in merged_df.columns:
    merged_df['Click Share (Niche)'] = merged_df['Click Share (Niche)'].combine_first(merged_df['Click Share (Niche) (Mining)'])
    merged_df.drop(columns=['Click Share (Niche) (Mining)'], inplace=True)

# (Aquí termina el código, no exporta, no imprime, solo modifica desde fila 3)
