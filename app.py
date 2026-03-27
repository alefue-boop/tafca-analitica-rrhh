import pandas as pd

# Definir las columnas estándar para el dashboard
columnas_maestras = [
    'Faena', 'RUT', 'Nombre', 'Cargo', 'Centro_Costo', 
    'Monto_Tratos', 'Monto_DT', 'Bonos', 'Gasto_Total', 'Descripcion'
]

# ==========================================
# PROCESAMIENTO UN 239
# ==========================================
# Saltamos 2 filas (la fila 3 será la cabecera)
df_239 = pd.read_csv('TRATOS UN 239.xls - Hoja1.csv', skiprows=2)

df_239 = df_239.rename(columns={
    'NOMBRE': 'Nombre',
    'CARGO': 'Cargo',
    'EQ. A CARGO': 'Centro_Costo',
    'Total Horas Trato': 'Monto_Tratos',
    'Valor a Pagar': 'Monto_DT',
    'BONOS': 'Bonos',
    'SUMA  TOTAL': 'Gasto_Total', # Ojo al doble espacio original
    'DESCRIPCION DE': 'Descripcion'
})
df_239 = df_239.reindex(columns=columnas_maestras)

# ==========================================
# PROCESAMIENTO UN 234 (AALL Rengo)
# ==========================================
# Saltamos 3 filas (la fila 4 será la cabecera)
df_234 = pd.read_csv('UN-234.xlsx - Hoja1.csv', skiprows=3)

df_234 = df_234.rename(columns={
    'NOMBRE': 'Nombre',
    'CARGO': 'Cargo',
    'GRUPO TRABAJO': 'Centro_Costo',
    'Sub Total': 'Monto_Tratos',
    'Sub Total.1': 'Monto_DT',
    'Bonos': 'Bonos',
    'TRATOS': 'Gasto_Total',          # En este archivo el total bajó a esta columna
    'LOS BONOS PAGADOS': 'Descripcion' # La descripción quedó con este nombre
})
df_234 = df_234.reindex(columns=columnas_maestras)

# ==========================================
# PROCESAMIENTO UN 227 (Marimaura / UN-224)
# ==========================================
# Saltamos 3 filas (la fila 4 será la cabecera)
df_227 = pd.read_csv('UN-224.xlsx - Hoja1.csv', skiprows=3)

df_227 = df_227.rename(columns={
    'NOMBRE': 'Nombre',
    'CARGO': 'Cargo',
    'GRUPO TRABAJO': 'Centro_Costo',
    'Sub Total': 'Monto_Tratos',
    'Sub Total.1': 'Monto_DT',
    'Otros': 'Bonos',                  # Aquí los bonos se llaman "Otros"
    'TOTAL': 'Gasto_Total',
    'DESCRIPCION DE': 'Descripcion'
})
df_227 = df_227.reindex(columns=columnas_maestras)

# ==========================================
# UNIFICACIÓN Y LIMPIEZA
# ==========================================
df_maestro = pd.concat([df_239, df_234, df_227], ignore_index=True)

# Limpiar RUTs vacíos
df_maestro = df_maestro.dropna(subset=['RUT'])

# Asegurar que los montos sean números y rellenar vacíos con 0
columnas_montos = ['Monto_Tratos', 'Monto_DT', 'Bonos', 'Gasto_Total']
for col in columnas_montos:
    # Convertir a número ignorando textos raros, transformando comas en puntos si es necesario
    df_maestro[col] = pd.to_numeric(df_maestro[col], errors='coerce').fillna(0)

# Filtrar para dejar solo trabajadores que efectivamente tuvieron tratos/bonos
df_maestro = df_maestro[df_maestro['Gasto_Total'] > 0]

# Rellenar descripciones vacías
df_maestro['Descripcion'] = df_maestro['Descripcion'].fillna('Sin descripción')
df_maestro.insert(0, 'Periodo', '2026-03')

# Exportar
df_maestro.to_csv('Base_Tratos_Consolidada.csv', index=False)
print("¡Listo! Archivos procesados correctamente.")
