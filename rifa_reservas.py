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

# CLAVE DEL VENDEDOR (configurable en secrets)
VENDEDOR_PASSWORD = st.secrets.get("VENDEDOR_PASSWORD", "vendedor123")

# Configuración de autenticación con Google Sheets
@st.cache_resource
def init_connection():
    """Inicializa la conexión con Google Sheets usando las credenciales del secrets"""
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        
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
    """Agrega una nueva venta/reserva a la hoja de cálculo"""
    try:
        sheet = gc.open_by_key(sheet_id)
        
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=worksheet_name, rows="1000", cols="10")
            headers = ["fecha", "vendedor", "numero", "nombre_comprador", "telefono", "email", "monto", "estado", "observaciones"]
            worksheet.append_row(headers)
        
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
        st.error(f"Error al guardar: {e}")
        return False

def update_number_status(gc, sheet_id, numero, new_status, vendedor_name="Vendedor", worksheet_name="ventas"):
    """Actualiza el estado de un número específico"""
    try:
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.worksheet(worksheet_name)
        
        # Obtener todos los datos
        all_values = worksheet.get_all_values()
        headers = all_values[0]
        
        # Buscar la fila del número
        numero_str = str(numero)
        for i, row in enumerate(all_values[1:], start=2):
            if str(row[2]) == numero_str:  # Columna 2 es 'numero'
                # Actualizar estado (columna 7) y vendedor (columna 1)
                worksheet.update_cell(i, 8, new_status)  # estado
                worksheet.update_cell(i, 2, vendedor_name)  # vendedor
                worksheet.update_cell(i, 1, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # fecha
                return True
        
        return False
    except Exception as e:
        st.error(f"Error al actualizar estado: {e}")
        return False

def get_numbers_by_status(df):
    """Obtiene números clasificados por estado"""
    if df.empty:
        return {
            'disponibles': list(range(1, 101)),
            'reservados': [],
            'vendidos': []
        }
    
    vendidos = df[df['estado'] == 'vendido']['numero'].astype(int).tolist()
    reservados = df[df['estado'] == 'reservado']['numero'].astype(int).tolist()
    todos = set(range(1, 101))
    ocupados = set(vendidos + reservados)
    disponibles = list(todos - ocupados)
    
    return {
        'disponibles': disponibles,
        'reservados': reservados,
        'vendidos': vendidos
    }

def get_sales_summary(df):
    """Genera resumen de ventas"""
    if df.empty:
        return {
            'total_vendidos': 0,
            'total_reservados': 0,
            'total_disponibles': 100,
            'monto_total': 0,
            'ventas_por_vendedor': {}
        }
    
    sold_df = df[df['estado'] == 'vendido']
    reserved_df = df[df['estado'] == 'reservado']
    
    summary = {
        'total_vendidos': len(sold_df),
        'total_reservados': len(reserved_df),
        'total_disponibles': 100 - len(sold_df) - len(reserved_df),
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
    
    .stats-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

def display_number_grid(disponibles, reservados, vendidos, total_numbers=100):
    """Muestra la grilla de números con tres estados"""
    st.markdown("### 🎯 Estado de los Números")
    
    # Leyenda
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟢 **Verde:** Disponible")
    with col2:
        st.markdown("🟡 **Amarillo:** Reservado")
    with col3:
        st.markdown("🔴 **Rojo:** Vendido")
    
    st.markdown("---")
    
    # Crear la grilla
    cols_per_row = 10
    rows = [list(range(i, min(i + cols_per_row, total_numbers + 1))) for i in range(1, total_numbers + 1, cols_per_row)]
    
    for row in rows:
        cols = st.columns(len(row))
        for i, num in enumerate(row):
            with cols[i]:
                if num in vendidos:
                    st.markdown(f'<div style="background-color: #ff6b6b; color: white; padding: 10px; text-align: center; border-radius: 5px; margin: 2px; font-weight: bold;">{num}</div>', unsafe_allow_html=True)
                elif num in reservados:
                    st.markdown(f'<div style="background-color: #ffd93d; color: black; padding: 10px; text-align: center; border-radius: 5px; margin: 2px; font-weight: bold;">{num}</div>', unsafe_allow_html=True)
                elif num in disponibles:
                    st.markdown(f'<div style="background-color: #51cf66; color: white; padding: 10px; text-align: center; border-radius: 5px; margin: 2px; font-weight: bold;">{num}</div>', unsafe_allow_html=True)

def main():
    # Cargar CSS
    load_css()
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🎟️ Rifa Multivendedor</h1>
        <p>Sistema de gestión de rifas con reservas y confirmación</p>
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
        ["🏠 Inicio", "📝 Reservar Número", "✅ Panel Vendedor", "📊 Administración"]
    )
    
    # Obtener datos actuales
    df = get_sheet_data(gc, sheet_id)
    numbers_status = get_numbers_by_status(df)
    summary = get_sales_summary(df)
    
    if page == "🏠 Inicio":
        # Página de inicio
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔴 Vendidos", summary['total_vendidos'])
        
        with col2:
            st.metric("🟡 Reservados", summary['total_reservados'])
        
        with col3:
            st.metric("🟢 Disponibles", summary['total_disponibles'])
        
        with col4:
            progress = (summary['total_vendidos'] + summary['total_reservados']) / 100 * 100
            st.metric("📈 Progreso", f"{progress:.1f}%")
        
        # Mostrar grilla de números
        display_number_grid(numbers_status['disponibles'], numbers_status['reservados'], numbers_status['vendidos'])
        
        # Información adicional
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Información de la Rifa")
            st.write("- **Total de números:** 100")
            st.write("- **Precio por número:** $10,000")
            st.write("- **Premio:** Por definir")
            st.write("- **Fecha de sorteo:** Por definir")
            st.write("")
            st.info("💡 **Instrucción:** Reserva tu número y el vendedor confirmará tu pago")
        
        with col2:
            st.markdown("### 💰 Recaudación")
            st.metric("Total Vendido", f"${summary['monto_total']:,.0f}")
            st.markdown("### 🏆 Top Vendedores")
            if summary['ventas_por_vendedor']:
                for vendedor, ventas in sorted(summary['ventas_por_vendedor'].items(), key=lambda x: x[1], reverse=True):
                    st.write(f"**{vendedor}:** {ventas} números")
            else:
                st.write("No hay ventas confirmadas aún")
    
    elif page == "📝 Reservar Número":
        st.markdown("### 📝 Reservar Número de Rifa")
        
        st.info("ℹ️ Al reservar un número, este quedará en estado **AMARILLO** hasta que el vendedor confirme tu pago y lo cambie a **ROJO** (vendido)")
        
        if not numbers_status['disponibles']:
            st.error("¡Lo sentimos! Todos los números han sido reservados o vendidos.")
            return
        
        with st.form("reserva_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Tus Datos**")
                nombre = st.text_input("Nombre completo *", placeholder="Ej: Juan Pérez")
                telefono = st.text_input("Teléfono *", placeholder="Ej: +54 11 1234-5678")
                email = st.text_input("Email", placeholder="tu@email.com")
                
            with col2:
                st.markdown("**Selección de Número**")
                numero_seleccionado = st.selectbox("Número a reservar *", sorted(numbers_status['disponibles']))
                monto = st.number_input("Monto a pagar ($)", value=10000, min_value=1000, disabled=True)
                observaciones = st.text_area("Observaciones", placeholder="Información adicional...")
            
            submitted = st.form_submit_button("🟡 Reservar Número", use_container_width=True, type="primary")
            
            if submitted:
                if not nombre or not telefono:
                    st.error("Por favor completa todos los campos obligatorios (*)")
                else:
                    # Preparar datos de reserva
                    sale_data = {
                        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "vendedor": "Pendiente confirmación",
                        "numero": numero_seleccionado,
                        "nombre_comprador": nombre,
                        "telefono": telefono,
                        "email": email,
                        "monto": monto,
                        "estado": "reservado",
                        "observaciones": observaciones
                    }
                    
                    # Guardar en Google Sheets
                    with st.spinner("Procesando reserva..."):
                        success = add_sale_to_sheet(gc, sheet_id, sale_data)
                    
                    if success:
                        st.success(f"✅ ¡Reserva exitosa! Número {numero_seleccionado} reservado para {nombre}")
                        st.info("📞 Un vendedor se contactará contigo para confirmar el pago")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Error al procesar la reserva. Intenta nuevamente.")
    
    elif page == "✅ Panel Vendedor":
        st.markdown("### ✅ Panel del Vendedor")
        
        # Sistema de autenticación
        if 'vendedor_logged' not in st.session_state:
            st.session_state.vendedor_logged = False
        
        if not st.session_state.vendedor_logged:
            st.warning("🔒 Acceso restringido. Ingresa la clave del vendedor.")
            
            with st.form("login_form"):
                password = st.text_input("Clave del Vendedor", type="password")
                vendedor_name = st.text_input("Tu Nombre", placeholder="Ej: Juan Vendedor")
                submit = st.form_submit_button("🔓 Ingresar")
                
                if submit:
                    if password == VENDEDOR_PASSWORD:
                        if vendedor_name:
                            st.session_state.vendedor_logged = True
                            st.session_state.vendedor_name = vendedor_name
                            st.success("✅ Acceso concedido")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Por favor ingresa tu nombre")
                    else:
                        st.error("❌ Clave incorrecta")
            
            st.info("💡 La clave por defecto es: `vendedor123` (configurable en secrets.toml)")
            return
        
        # Panel del vendedor autenticado
        vendedor_name = st.session_state.vendedor_name
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"👤 Sesión iniciada como: **{vendedor_name}**")
        with col2:
            if st.button("🚪 Cerrar Sesión"):
                st.session_state.vendedor_logged = False
                st.rerun()
        
        st.markdown("---")
        
        # Tabs para organizar funciones
        tab1, tab2, tab3 = st.tabs(["🟡 Confirmar Reservas", "🔴 Ventas Directas", "📊 Mis Estadísticas"])
        
        with tab1:
            st.markdown("#### 🟡 Números Reservados (Pendientes de Confirmación)")
            
            if not df.empty:
                reservados_df = df[df['estado'] == 'reservado'].copy()
                
                if not reservados_df.empty:
                    for idx, row in reservados_df.iterrows():
                        with st.expander(f"🟡 Número {row['numero']} - {row['nombre_comprador']}"):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**Cliente:** {row['nombre_comprador']}")
                                st.write(f"**Teléfono:** {row['telefono']}")
                                st.write(f"**Email:** {row['email']}")
                                st.write(f"**Monto:** ${row['monto']}")
                                st.write(f"**Fecha reserva:** {row['fecha']}")
                                if row['observaciones']:
                                    st.write(f"**Observaciones:** {row['observaciones']}")
                            
                            with col2:
                                if st.button(f"✅ Confirmar Venta", key=f"confirm_{row['numero']}"):
                                    success = update_number_status(gc, sheet_id, row['numero'], 'vendido', vendedor_name)
                                    if success:
                                        st.success(f"✅ Número {row['numero']} confirmado como VENDIDO")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Error al actualizar")
                else:
                    st.info("No hay números reservados pendientes de confirmación")
            else:
                st.info("No hay datos disponibles")
        
        with tab2:
            st.markdown("#### 🔴 Marcar Números como Vendidos")
            st.info("Usa esta opción para ventas directas o para confirmar números que ya cobraste")
            
            with st.form("venta_directa_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Mostrar números disponibles Y reservados
                    numeros_vendibles = sorted(numbers_status['disponibles'] + numbers_status['reservados'])
                    numero_venta = st.selectbox("Número a marcar como VENDIDO", numeros_vendibles)
                    nombre_comprador = st.text_input("Nombre del comprador *")
                    telefono_comprador = st.text_input("Teléfono *")
                
                with col2:
                    email_comprador = st.text_input("Email (opcional)")
                    monto_venta = st.number_input("Monto ($)", value=10000, min_value=1000)
                    obs_venta = st.text_area("Observaciones")
                
                if st.form_submit_button("🔴 Confirmar como VENDIDO", type="primary"):
                    if nombre_comprador and telefono_comprador:
                        # Primero verificar si el número ya existe en la hoja
                        numero_existe = not df.empty and numero_venta in df['numero'].astype(int).tolist()
                        
                        if numero_existe:
                            # Solo actualizar el estado
                            success = update_number_status(gc, sheet_id, numero_venta, 'vendido', vendedor_name)
                        else:
                            # Crear nueva entrada
                            sale_data = {
                                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "vendedor": vendedor_name,
                                "numero": numero_venta,
                                "nombre_comprador": nombre_comprador,
                                "telefono": telefono_comprador,
                                "email": email_comprador,
                                "monto": monto_venta,
                                "estado": "vendido",
                                "observaciones": obs_venta
                            }
                            success = add_sale_to_sheet(gc, sheet_id, sale_data)
                        
                        if success:
                            st.success(f"✅ Número {numero_venta} marcado como VENDIDO")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Error al procesar")
                    else:
                        st.error("Completa todos los campos obligatorios")
        
        with tab3:
            st.markdown("#### 📊 Mis Estadísticas")
            
            if not df.empty:
                mis_ventas = df[df['vendedor'] == vendedor_name]
                mis_ventas_confirmadas = mis_ventas[mis_ventas['estado'] == 'vendido']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Números Vendidos", len(mis_ventas_confirmadas))
                
                with col2:
                    total_vendido = mis_ventas_confirmadas['monto'].astype(float).sum() if not mis_ventas_confirmadas.empty else 0
                    st.metric("Total Recaudado", f"${total_vendido:,.0f}")
                
                with col3:
                    comision = total_vendido * 0.1
                    st.metric("Comisión (10%)", f"${comision:,.0f}")
                
                st.markdown("---")
                st.markdown("**Historial de Ventas**")
                if not mis_ventas_confirmadas.empty:
                    st.dataframe(mis_ventas_confirmadas, use_container_width=True, hide_index=True)
                else:
                    st.info("Aún no tienes ventas confirmadas")
            else:
                st.info("No hay datos disponibles")
    
    elif page == "📊 Administración":
        st.markdown("### 📊 Panel de Administración")
        
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🔴 Vendidos", summary['total_vendidos'])
        with col2:
            st.metric("🟡 Reservados", summary['total_reservados'])
        with col3:
            st.metric("💰 Recaudación", f"${summary['monto_total']:,.0f}")
        with col4:
            efficiency = (summary['total_vendidos'] / 100) * 100
            st.metric("Eficiencia", f"{efficiency:.1f}%")
        
        # Datos completos
        st.markdown("### 📋 Datos Completos")
        if not df.empty:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                vendedor_filter = st.selectbox("Filtrar por vendedor", ["Todos"] + list(df['vendedor'].unique()))
            with col2:
                estado_filter = st.selectbox("Filtrar por estado", ["Todos", "vendido", "reservado"])
            
            # Aplicar filtros
            df_admin = df.copy()
            if vendedor_filter != "Todos":
                df_admin = df_admin[df_admin['vendedor'] == vendedor_filter]
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
                    if numbers_status['vendidos']:
                        ganador = random.choice(numbers_status['vendidos'])
                        winner_data = df[df['numero'].astype(int) == ganador].iloc[0]
                        st.success(f"🏆 ¡Número ganador: {ganador}!")
                        st.info(f"Ganador: {winner_data['nombre_comprador']} - Tel: {winner_data['telefono']}")
                    else:
                        st.warning("No hay números vendidos para sortear")
            
            with col2:
                st.markdown("**Info Sistema**")
                st.write(f"Clave vendedor: `{VENDEDOR_PASSWORD}`")
                st.caption("(Configurable en secrets.toml)")

if __name__ == "__main__":
    main()
