import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control de Tratos - Tafca SPA", layout="wide")
st.title("Consolidador Global de Tratos por Unidad de Negocio")

st.info("Sube todos los reportes de Excel de las distintas obras al mismo tiempo.")

# Un solo cargador que acepta MÚLTIPLES archivos
archivos_subidos = st.file_uploader(
    "Arrastra aquí los archivos (.xls, .xlsx o .csv)", 
    type=['xls', 'xlsx', 'csv'], 
    accept_multiple_files=True
)

if archivos_subidos:
    lista_dfs = []
    
    for archivo in archivos_subidos:
        nombre_ext = archivo.name.upper()
        
        try:
            # 1. Leer las primeras 15 filas para buscar DÓNDE empieza realmente la tabla
            if '.CSV' in nombre_ext:
                temp_df = pd.read_csv(archivo, nrows=15, header=None)
            else:
                temp_df = pd.read_excel(archivo, nrows=15, header=None)
                
            fila_cabecera = 0
            # Buscamos la fila que contenga la palabra "RUT"
            for i in range(len(temp_df)):
                valores_fila = temp_df.iloc[i].astype(str).str.upper().values
                if 'RUT' in valores_fila:
                    fila_cabecera = i
                    break
            
            # 2. Volver a leer el archivo desde la fila exacta que encontramos
            archivo.seek(0)
            if '.CSV' in nombre_ext:
                df = pd.read_csv(archivo, skiprows=fila_cabecera)
            else:
                df = pd.read_excel(archivo, skiprows=fila_cabecera)
                
            # Limpiar nombres de columnas (quitar espacios extra y pasar a mayúsculas)
            df.columns = df.columns.astype(str).str.strip().str.upper()
            
            # 3. Mapeo Dinámico (Resiste cambios en los nombres de las columnas)
            df_std = pd.DataFrame()
            
            # Forzar la Faena a ser TEXTO para que el gráfico las separe correctamente
            if 'FAENA' in df.columns:
                df_std['Faena'] = df['FAENA'].astype(str).str.replace('.0', '', regex=False).str.strip()
            else:
                df_std['Faena'] = "Sin Faena"
                
            df_std['RUT'] = df['RUT'] if 'RUT' in df.columns else None
            df_std['Nombre'] = df['NOMBRE'] if 'NOMBRE' in df.columns else "Desconocido"
            
            # Monto Tratos
            if 'TOTAL HORAS TRATO' in df.columns:
                df_std['Monto_Tratos'] = df['TOTAL HORAS TRATO']
            elif 'SUB TOTAL' in df.columns: # Toma el primer sub total que encuentre
                df_std['Monto_Tratos'] = df['SUB TOTAL']
            else:
                df_std['Monto_Tratos'] = 0
                
            # Gasto Total
            if 'SUMA  TOTAL' in df.columns:
                df_std['Gasto_Total'] = df['SUMA  TOTAL']
            elif 'SUMA TOTAL' in df.columns:
                df_std['Gasto_Total'] = df['SUMA TOTAL']
            elif 'TRATOS' in df.columns:
                df_std['Gasto_Total'] = df['TRATOS']
            elif 'TOTAL' in df.columns:
                df_std['Gasto_Total'] = df['TOTAL']
            else:
                df_std['Gasto_Total'] = 0
                
            lista_dfs.append(df_std)
            
        except Exception as e:
            st.error(f"No se pudo procesar el archivo {archivo.name}. Error: {e}")

    # --- UNIFICACIÓN DE TODAS LAS OBRAS ---
    if lista_dfs:
        df_maestro = pd.concat(lista_dfs, ignore_index=True)
        
        # Limpieza final
        df_maestro = df_maestro.dropna(subset=['RUT'])
        df_maestro['Monto_Tratos'] = pd.to_numeric(df_maestro['Monto_Tratos'], errors='coerce').fillna(0)
        df_maestro['Gasto_Total'] = pd.to_numeric(df_maestro['Gasto_Total'], errors='coerce').fillna(0)
        df_maestro = df_maestro[df_maestro['Gasto_Total'] > 0]
        
        st.success("¡Información de TODAS las obras unificada correctamente!")
        st.divider()

        # --- ANÁLISIS POR UNIDAD DE NEGOCIO ---
        st.subheader("Análisis de Gasto por Unidad de Negocio (Faena)")
        
        # Agrupamos los datos explícitamente por Faena
        analisis_obras = df_maestro.groupby('Faena').agg(
            Trabajadores=('RUT', 'count'),
            Gasto_Total=('Gasto_Total', 'sum')
        ).reset_index()
        
        col_tabla, col_grafico = st.columns([1, 2])
        
        with col_tabla:
            st.write("**Detalle por Obra**")
            # Mostramos la tabla formateada para comprobar que leyó todas las faenas
            st.dataframe(
                analisis_obras.style.format({'Gasto_Total': '${:,.0f}'}),
                use_container_width=True,
                hide_index=True
            )
            
        with col_grafico:
            st.write("**Comparativa de Gasto Total**")
            # Al ser texto, el gráfico mostrará barras separadas e independientes
        st.bar_chart(analisis_obras, x='Faena', y='Gasto_Total', color="#FF4B4B")
