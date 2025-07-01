import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import datetime
import random
import time
from typing import Dict, List, Any

# Configuración de la página
st.set_page_config(
    page_title="Rifa Multivendedor",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de autenticación con Google Sheets
@st.cache_resource
def init_connection():
    """Inicializa la conexión con Google Sheets usando las credenciales del secrets"""
    try:
        # Configurar credenciales desde st.secrets
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        
        # Conectar con Google Sheets
        gc = gspread.authorize(credentials)
        sheet_id = st.secrets["GOOGLE_SHEET_ID"]
        return gc, sheet_id
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None, None

def get_sheet_data(gc, sheet_id, worksheet_name="ventas"):
    """Obtiene datos de la hoja de cálculo"""
    try:
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error al obtener datos: {e}")
        return pd.DataFrame()

def add_sale_to_sheet(gc, sheet_id, sale_data, worksheet_name="ventas"):
    """Agrega una nueva venta a la hoja de cálculo"""
    try:
        sheet = gc.open_by_key(sheet_id)
        
        # Intentar acceder a la hoja, si no existe la creamos
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            # Crear hoja con headers
            worksheet = sheet.add_worksheet(title=worksheet_name, rows="1000", cols="10")
            headers = ["fecha", "vendedor", "numero", "nombre_comprador", "telefono", "email", "monto", "estado", "observaciones"]
            worksheet.append_row(headers)
        
        # Agregar nueva fila
        row_data = [
            sale_data["fecha"],
            sale_data["vendedor"],
            sale_data["numero"],
            sale_data["nombre_comprador"],
            sale_data["telefono"],
            sale_data["email"],
            sale_data["monto"],
            sale_data["estado"],
            sale_data.get("observaciones", "")
        ]
        worksheet.append_row(row_data)
        return True
    except Exception as e:
        st.error(f"Error al guardar venta: {e}")
        return False

def get_available_numbers(df, total_numbers=100):
    """Obtiene los números disponibles para la rifa"""
    if df.empty:
        return list(range(1, total_numbers + 1))
    
    sold_numbers = df[df['estado'] == 'vendido']['numero'].astype(int).tolist()
    available = [num for num in range(1, total_numbers + 1) if num not in sold_numbers]
    return available

def get_sales_summary(df):
    """Genera resumen de ventas"""
    if df.empty:
        return {
            'total_vendidos': 0,
            'total_disponibles': 100,
            'monto_total': 0,
            'ventas_por_vendedor': {}
        }
    
    sold_df = df[df['estado'] == 'vendido']
    
    summary = {
        'total_vendidos': len(sold_df),
        'total_disponibles': 100 - len(sold_df),
        'monto_total': sold_df['monto'].astype(float).sum() if not sold_df.empty else 0,
        'ventas_por_vendedor': sold_df.groupby('vendedor').size().to_dict() if not sold_df.empty else {}
    }
    
    return summary

# CSS personalizado
def load_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .number-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 5px;
        margin: 1rem 0;
    }
    
    .number-cell {
        background-color: #f0f2f6;
        padding: 10px;
        text-align: center;
        border-radius: 5px;
        border: 1px solid #ddd;
    }
    
    .number-sold {
        background-color: #ff6b6b;
        color: white;
    }
    
    .number-available {
        background-color: #51cf66;
        color: white;
        cursor: pointer;
    }
    
    .stats-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .vendor-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def display_number_grid(available_numbers, sold_numbers, total_numbers=100):
    """Muestra la grilla de números de la rifa"""
    st.markdown("### 🎯 Estado de los Números")
    
    # Crear la grilla usando columnas de Streamlit
    cols_per_row = 10
    rows = [list(range(i, min(i + cols_per_row, total_numbers + 1))) for i in range(1, total_numbers + 1, cols_per_row)]
    
    for row in rows:
        cols = st.columns(len(row))
        for i, num in enumerate(row):
            with cols[i]:
                if num in sold_numbers:
                    st.markdown(f'<div style="background-color: #ff6b6b; color: white; padding: 10px; text-align: center; border-radius: 5px; margin: 2px;">{num}</div>', unsafe_allow_html=True)
                elif num in available_numbers:
                    st.markdown(f'<div style="background-color: #51cf66; color: white; padding: 10px; text-align: center; border-radius: 5px; margin: 2px;">{num}</div>', unsafe_allow_html=True)

def main():
    # Cargar CSS
    load_css()
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🎟️ Rifa Multivendedor</h1>
        <p>Sistema de gestión de rifas con múltiples vendedores</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar conexión
    gc, sheet_id = init_connection()
    
    if gc is None or sheet_id is None:
        st.error("No se pudo establecer conexión con Google Sheets. Verifica la configuración.")
        return
    
    # Sidebar para navegación
    st.sidebar.title("🎯 Navegación")
    page = st.sidebar.selectbox(
        "Selecciona una opción:",
        ["🏠 Inicio", "🛒 Comprar Número", "👥 Panel Vendedor", "📊 Administración"]
    )
    
    # Obtener datos actuales
    df = get_sheet_data(gc, sheet_id)
    available_numbers = get_available_numbers(df)
    sold_numbers = df[df['estado'] == 'vendido']['numero'].astype(int).tolist() if not df.empty else []
    summary = get_sales_summary(df)
    
    if page == "🏠 Inicio":
        # Página de inicio
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Números Vendidos", summary['total_vendidos'])
        
        with col2:
            st.metric("✅ Números Disponibles", summary['total_disponibles'])
        
        with col3:
            st.metric("💰 Recaudación Total", f"${summary['monto_total']:,.0f}")
        
        with col4:
            progress = summary['total_vendidos'] / 100 * 100
            st.metric("📈 Progreso", f"{progress:.1f}%")
        
        # Mostrar grilla de números
        display_number_grid(available_numbers, sold_numbers)
        
        # Información adicional
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Información de la Rifa")
            st.write("- **Total de números:** 100")
            st.write("- **Precio por número:** $10,000")
            st.write("- **Premio:** Por definir")
            st.write("- **Fecha de sorteo:** Por definir")
        
        with col2:
            st.markdown("### 🏆 Top Vendedores")
            if summary['ventas_por_vendedor']:
                for vendedor, ventas in sorted(summary['ventas_por_vendedor'].items(), key=lambda x: x[1], reverse=True):
                    st.write(f"**{vendedor}:** {ventas} números")
            else:
                st.write("No hay ventas registradas aún")
    
    elif page == "🛒 Comprar Número":
        st.markdown("### 🛒 Comprar Número de Rifa")
        
        if not available_numbers:
            st.error("¡Lo sentimos! Todos los números han sido vendidos.")
            return
        
        with st.form("compra_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Información del Comprador**")
                nombre = st.text_input("Nombre completo *")
                telefono = st.text_input("Teléfono *")
                email = st.text_input("Email")
                
            with col2:
                st.markdown("**Detalles de la Compra**")
                vendedor = st.selectbox("Vendedor *", ["Vendedor 1", "Vendedor 2", "Vendedor 3", "Otro"])
                if vendedor == "Otro":
                    vendedor = st.text_input("Nombre del vendedor")
                
                numero_seleccionado = st.selectbox("Número a comprar *", available_numbers)
                monto = st.number_input("Monto ($)", value=10000, min_value=1000)
                observaciones = st.text_area("Observaciones", placeholder="Información adicional...")
            
            submitted = st.form_submit_button("💳 Confirmar Compra", use_container_width=True)
            
            if submitted:
                if not nombre or not telefono or not vendedor:
                    st.error("Por favor completa todos los campos obligatorios (*)")
                else:
                    # Preparar datos de venta
                    sale_data = {
                        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "vendedor": vendedor,
                        "numero": numero_seleccionado,
                        "nombre_comprador": nombre,
                        "telefono": telefono,
                        "email": email,
                        "monto": monto,
                        "estado": "vendido",
                        "observaciones": observaciones
                    }
                    
                    # Guardar en Google Sheets
                    with st.spinner("Procesando compra..."):
                        success = add_sale_to_sheet(gc, sheet_id, sale_data)
                    
                    if success:
                        st.success(f"¡Compra exitosa! Número {numero_seleccionado} vendido a {nombre}")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Error al procesar la compra. Intenta nuevamente.")
    
    elif page == "👥 Panel Vendedor":
        st.markdown("### 👥 Panel del Vendedor")
        
        vendedor_filter = st.selectbox("Seleccionar Vendedor", 
                                     ["Todos"] + list(summary['ventas_por_vendedor'].keys()) + ["Vendedor 1", "Vendedor 2", "Vendedor 3"])
        
        if vendedor_filter != "Todos" and not df.empty:
            df_filtered = df[df['vendedor'] == vendedor_filter]
        else:
            df_filtered = df
        
        # Estadísticas del vendedor
        if vendedor_filter != "Todos":
            col1, col2, col3 = st.columns(3)
            vendedor_sales = df_filtered[df_filtered['estado'] == 'vendido'] if not df_filtered.empty else pd.DataFrame()
            
            with col1:
                st.metric("Números Vendidos", len(vendedor_sales))
            with col2:
                total_vendedor = vendedor_sales['monto'].astype(float).sum() if not vendedor_sales.empty else 0
                st.metric("Total Recaudado", f"${total_vendedor:,.0f}")
            with col3:
                comision = total_vendedor * 0.1  # 10% de comisión
                st.metric("Comisión (10%)", f"${comision:,.0f}")
        
        # Tabla de ventas
        st.markdown("### 📊 Registro de Ventas")
        if not df_filtered.empty:
            st.dataframe(
                df_filtered,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay ventas registradas para este vendedor")
        
        # Botón para agregar venta manual
        with st.expander("➕ Agregar Venta Manual"):
            with st.form("venta_manual"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nombre_manual = st.text_input("Nombre del comprador")
                    telefono_manual = st.text_input("Teléfono")
                    vendedor_manual = st.text_input("Vendedor", value=vendedor_filter if vendedor_filter != "Todos" else "")
                
                with col2:
                    numero_manual = st.selectbox("Número", available_numbers)
                    monto_manual = st.number_input("Monto", value=10000)
                    email_manual = st.text_input("Email (opcional)")
                
                if st.form_submit_button("Guardar Venta"):
                    if nombre_manual and telefono_manual and vendedor_manual:
                        sale_data = {
                            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "vendedor": vendedor_manual,
                            "numero": numero_manual,
                            "nombre_comprador": nombre_manual,
                            "telefono": telefono_manual,
                            "email": email_manual,
                            "monto": monto_manual,
                            "estado": "vendido",
                            "observaciones": "Venta manual"
                        }
                        
                        success = add_sale_to_sheet(gc, sheet_id, sale_data)
                        if success:
                            st.success("Venta agregada exitosamente")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.error("Completa todos los campos requeridos")
    
    elif page == "📊 Administración":
        st.markdown("### 📊 Panel de Administración")
        
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Vendidos", summary['total_vendidos'], f"{summary['total_vendidos']-90} vs objetivo")
        with col2:
            st.metric("Recaudación", f"${summary['monto_total']:,.0f}")
        with col3:
            efficiency = (summary['total_vendidos'] / 100) * 100
            st.metric("Eficiencia", f"{efficiency:.1f}%")
        with col4:
            st.metric("Vendedores Activos", len(summary['ventas_por_vendedor']))
        
        # Datos completos
        st.markdown("### 📋 Datos Completos")
        if not df.empty:
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                date_filter = st.date_input("Filtrar por fecha")
            with col2:
                vendedor_admin_filter = st.selectbox("Filtrar por vendedor", ["Todos"] + list(df['vendedor'].unique()))
            with col3:
                estado_filter = st.selectbox("Filtrar por estado", ["Todos", "vendido", "reservado", "cancelado"])
            
            # Aplicar filtros
            df_admin = df.copy()
            if vendedor_admin_filter != "Todos":
                df_admin = df_admin[df_admin['vendedor'] == vendedor_admin_filter]
            if estado_filter != "Todos":
                df_admin = df_admin[df_admin['estado'] == estado_filter]
            
            st.dataframe(df_admin, use_container_width=True, hide_index=True)
            
            # Botón de descarga
            csv = df_admin.to_csv(index=False)
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"reporte_rifa_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay datos para mostrar")
        
        # Herramientas administrativas
        with st.expander("🛠️ Herramientas Administrativas"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Sorteo**")
                if st.button("🎲 Realizar Sorteo"):
                    if sold_numbers:
                        ganador = random.choice(sold_numbers)
                        winner_data = df[df['numero'].astype(int) == ganador].iloc[0]
                        st.success(f"🏆 ¡Número ganador: {ganador}!")
                        st.info(f"Ganador: {winner_data['nombre_comprador']} - Tel: {winner_data['telefono']}")
                    else:
                        st.warning("No hay números vendidos para sortear")
            
            with col2:
                st.markdown("**Resetear Datos**")
                if st.button("🗑️ Limpiar Datos", type="secondary"):
                    st.warning("Esta función eliminaría todos los datos. Implementar con cuidado.")

if __name__ == "__main__":
    main()
