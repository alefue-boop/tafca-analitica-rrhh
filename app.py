import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control de Tratos - Tafca SPA", layout="wide")
st.title("Consolidador Global de Tratos por Obra")

st.info("Sube aquí los archivos (.xls, .xlsx o .csv) de todas las obras al mismo tiempo.")

archivos_subidos = st.file_uploader(
    "Arrastra los archivos de asistencia", 
    type=['xls', 'xlsx', 'csv'], 
    accept_multiple_files=True
)

if archivos_subidos:
    lista_dfs = []
    
    for archivo in archivos_subidos:
        nombre_ext = archivo.name.upper()
        try:
            # Leer el archivo temporalmente sin cabeceras
            if '.CSV' in nombre_ext:
                df_raw = pd.read_csv(archivo, header=None)
            else:
                df_raw = pd.read_excel(archivo, header=None)
                
            # 1. Buscar la fila exacta que contiene la palabra 'RUT'
            fila_rut = -1
            for i in range(min(15, len(df_raw))):
                valores = df_raw.iloc[i].astype(str).str.upper().values
                if 'RUT' in valores:
                    fila_rut = i
                    break
                    
            if fila_rut > 0:
                # 2. FUSIONAR CABECERAS: Une la fila de arriba con la fila del RUT 
                # Esto soluciona el problema de la UN 239 donde "SUMA" y "TOTAL" están en filas separadas
                h1 = df_raw.iloc[fila_rut - 1].fillna('').astype(str).str.strip().str.upper()
                h2 = df_raw.iloc[fila_rut].fillna('').astype(str).str.strip().str.upper()
                
                nuevas_cabeceras = []
                for a, b in zip(h1, h2):
                    # Limpiar dobles espacios (ej. "SUMA  TOTAL" pasa a "SUMA TOTAL")
                    a = " ".join(a.split()) 
                    b = " ".join(b.split())
                    
                    if a and b and a != b: nuevas_cabeceras.append(f"{a} {b}")
                    elif b: nuevas_cabeceras.append(b)
                    elif a: nuevas_cabeceras.append(a)
                    else: nuevas_cabeceras.append("VACIO")
                    
                df_raw.columns = nuevas_cabeceras
                df = df_raw.iloc[fila_rut + 1:].reset_index(drop=True)
            else:
                df_raw.columns = df_raw.iloc[0].fillna('').astype(str).str.strip().str.upper()
                df = df_raw.iloc[1:].reset_index(drop=True)

            # 3. Mapear las columnas encontradas a la Base Maestra
            df_std = pd.DataFrame()
            cols = df.columns
            
            # Faena
            col_faena = [c for c in cols if 'FAENA' in c]
            df_std['Faena'] = df[col_faena[0]].astype(str).str.replace('.0', '', regex=False).str.strip() if col_faena else "Sin Faena"
            
            # RUT, Nombre y Cargo
            col_rut = [c for c in cols if 'RUT' in c]
            df_std['RUT'] = df[col_rut[0]] if col_rut else None
            
            col_nombre = [c for c in cols if 'NOMBRE' in c]
            df_std['Nombre'] = df[col_nombre[0]] if col_nombre else "Desconocido"
            
            col_cargo = [c for c in cols if 'CARGO' in c]
            df_std['Cargo'] = df[col_cargo[0]] if col_cargo else "Sin Cargo"
            
            # Capturar el Gasto Total adaptándose a los nombres de las 3 obras
            if 'SUMA TOTAL' in cols:
                df_std['Gasto_Total'] = df['SUMA TOTAL']
            elif 'TOTAL TRATOS' in cols:
                df_std['Gasto_Total'] = df['TOTAL TRATOS']
            elif 'TOTAL' in cols:
                df_std['Gasto_Total'] = df['TOTAL']
            elif 'TRATOS' in cols:
                df_std['Gasto_Total'] = df['TRATOS']
            else:
                df_std['Gasto_Total'] = 0
                
            lista_dfs.append(df_std)
            
        except Exception as e:
            st.error(f"Error procesando {archivo.name}: {e}")

    # --- UNIFICACIÓN Y VISUALIZACIÓN ---
    if lista_dfs:
        df_maestro = pd.concat(lista_dfs, ignore_index=True)
        
        # Limpieza: eliminar filas sin RUT y convertir a números
        df_maestro = df_maestro.dropna(subset=['RUT'])
        df_maestro = df_maestro[df_maestro['RUT'].astype(str).str.strip() != '']
        df_maestro['Gasto_Total'] = pd.to_numeric(df_maestro['Gasto_Total'], errors='coerce').fillna(0)
        
        # Dejar solo a los trabajadores que efectivamente tuvieron un cobro por tratos
        df_maestro = df_maestro[df_maestro['Gasto_Total'] > 0]
        
        st.success("¡Información de todas las obras unificada correctamente!")
        
        # --- PANEL DE RESUMEN ---
        col_tabla, col_grafico = st.columns([1, 2])
        
        with col_tabla:
            st.subheader("Gasto por Faena")
            gasto_faena = df_maestro.groupby('Faena').agg(
                Trabajadores=('RUT', 'count'),
                Gasto_Total=('Gasto_Total', 'sum')
            ).reset_index()
            st.dataframe(gasto_faena.style.format({'Gasto_Total': '${:,.0f}'}), use_container_width=True, hide_index=True)
            
        with col_grafico:
            st.subheader("Comparativa de Gasto")
            st.bar_chart(gasto_faena, x='Faena', y='Gasto_Total', color="#FF4B4B")
            
        st.divider()
        
        # --- TABLA DETALLADA POR TRABAJADOR ---
        st.subheader("Detalle por Trabajadores")
        st.write("Visualiza el gasto exacto de cada trabajador. Puedes filtrar por unidad de negocio.")
        
        obra_filtro = st.selectbox("Filtrar por Unidad de Negocio", ["Todas las Obras"] + list(df_maestro['Faena'].unique()))
        
        if obra_filtro != "Todas las Obras":
            df_mostrar = df_maestro[df_maestro['Faena'] == obra_filtro]
        else:
            df_mostrar = df_maestro
            
        # Ordenamos de mayor a menor gasto para facilitar el control
        df_mostrar = df_mostrar.sort_values(by='Gasto_Total', ascending=False)
        
        st.dataframe(
            df_mostrar.style.format({'Gasto_Total': '${:,.0f}'}),
            use_container_width=True,
            hide_index=True
        )
