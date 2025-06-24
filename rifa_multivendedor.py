import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import time
import json

# Configuración de la página
st.set_page_config(
    page_title="Rifa Multi-Vendedor",
    page_icon="🎲",
    layout="wide"
)

# Configuración de Google Sheets
@st.cache_resource
def init_google_sheets():
    """Inicializa la conexión con Google Sheets usando st.secrets"""
    try:
        # Las credenciales se configuran en Streamlit.app secrets
        credentials_dict = st.secrets["gcp_service_account"]
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        
        client = gspread.authorize(credentials)
        
        # ID de tu Google Sheet (configurable en secrets)
        sheet_id = st.secrets["google_sheet_id"]
        sheet = client.open_by_key(sheet_id)
        
        return sheet
    except Exception as e:
        st.error(f"Error conectando con Google Sheets: {e}")
        st.info("Configurar las credenciales en Streamlit secrets:")
        st.code("""
[gcp_service_account]
type = "service_account"
project_id = "tu-proyecto"
private_key_id = "key-id"
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "email@proyecto.iam.gserviceaccount.com"
client_id = "client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"

google_sheet_id = "1ABC123XYZ456..."
        """)
        return None

class RifaManager:
    def __init__(self, sheet):
        self.sheet = sheet
        self.ventas_worksheet = None
        self.reservas_worksheet = None
        self.init_worksheets()
    
    def init_worksheets(self):
        """Inicializa las hojas de trabajo"""
        try:
            # Hoja de ventas confirmadas
            try:
                self.ventas_worksheet = self.sheet.worksheet("ventas")
            except gspread.WorksheetNotFound:
                self.ventas_worksheet = self.sheet.add_worksheet(
                    title="ventas", rows=200, cols=10
                )
                self.ventas_worksheet.append_row([
                    "numero", "comprador", "telefono", "vendedor", 
                    "fecha_venta", "timestamp"
                ])
            
            # Hoja de reservas temporales (evitar sobreventa)
            try:
                self.reservas_worksheet = self.sheet.worksheet("reservas")
            except gspread.WorksheetNotFound:
                self.reservas_worksheet = self.sheet.add_worksheet(
                    title="reservas", rows=200, cols=10
                )
                self.reservas_worksheet.append_row([
                    "numero", "vendedor", "timestamp_reserva", "expira_en"
                ])
                
        except Exception as e:
            st.error(f"Error inicializando worksheets: {e}")
    
    def limpiar_reservas_expiradas(self):
        """Limpia reservas que han expirado"""
        try:
            records = self.reservas_worksheet.get_all_records()
            now = datetime.now()
            
            rows_to_delete = []
            for i, record in enumerate(records):
                expira = datetime.fromisoformat(record['expira_en'])
                if now > expira:
                    rows_to_delete.append(i + 2)  # +2 porque índice empieza en 1 y hay header
            
            # Eliminar filas expiradas (de atrás hacia adelante)
            for row_num in reversed(rows_to_delete):
                self.reservas_worksheet.delete_rows(row_num)
                
        except Exception as e:
            st.warning(f"Error limpiando reservas: {e}")
    
    def obtener_numeros_vendidos(self):
        """Obtiene números ya vendidos definitivamente"""
        try:
            records = self.ventas_worksheet.get_all_records()
            return {int(record['numero']): record for record in records if record['numero']}
        except:
            return {}
    
    def obtener_numeros_reservados(self):
        """Obtiene números temporalmente reservados"""
        try:
            self.limpiar_reservas_expiradas()
            records = self.reservas_worksheet.get_all_records()
            return {int(record['numero']): record for record in records if record['numero']}
        except:
            return {}
    
    def reservar_numero(self, numero, vendedor, minutos=5):
        """Reserva un número temporalmente"""
        try:
            # Verificar si ya está vendido o reservado
            vendidos = self.obtener_numeros_vendidos()
            reservados = self.obtener_numeros_reservados()
            
            if numero in vendidos:
                return False, "Número ya vendido"
            
            if numero in reservados:
                return False, f"Número reservado por {reservados[numero]['vendedor']}"
            
            # Crear reserva
            now = datetime.now()
            expira = now + timedelta(minutes=minutos)
            
            self.reservas_worksheet.append_row([
                numero, vendedor, now.isoformat(), expira.isoformat()
            ])
            
            return True, "Número reservado exitosamente"
            
        except Exception as e:
            return False, f"Error reservando: {e}"
    
    def confirmar_venta(self, numero, comprador, telefono, vendedor):
        """Confirma una venta y elimina la reserva"""
        try:
            # Verificar que el vendedor tiene la reserva
            reservados = self.obtener_numeros_reservados()
            if numero not in reservados:
                return False, "Número no está reservado"
            
            if reservados[numero]['vendedor'] != vendedor:
                return False, "No tienes la reserva de este número"
            
            # Agregar a ventas
            now = datetime.now()
            self.ventas_worksheet.append_row([
                numero, comprador, telefono, vendedor, 
                now.strftime("%Y-%m-%d %H:%M:%S"), now.isoformat()
            ])
            
            # Eliminar reserva
            self.cancelar_reserva(numero, vendedor)
            
            return True, "Venta confirmada exitosamente"
            
        except Exception as e:
            return False, f"Error confirmando venta: {e}"
    
    def cancelar_reserva(self, numero, vendedor):
        """Cancela una reserva específica"""
        try:
            records = self.reservas_worksheet.get_all_records()
            for i, record in enumerate(records):
                if (int(record['numero']) == numero and 
                    record['vendedor'] == vendedor):
                    self.reservas_worksheet.delete_rows(i + 2)
                    break
        except Exception as e:
            st.warning(f"Error cancelando reserva: {e}")

# Inicializar componentes
@st.cache_resource
def get_rifa_manager():
    sheet = init_google_sheets()
    if sheet:
        return RifaManager(sheet)
    return None

# Inicializar session state
if 'vendedor' not in st.session_state:
    st.session_state.vendedor = ""
if 'ultima_actualizacion' not in st.session_state:
    st.session_state.ultima_actualizacion = datetime.now()
if 'numero_reservado' not in st.session_state:
    st.session_state.numero_reservado = None
if 'tiempo_reserva' not in st.session_state:
    st.session_state.tiempo_reserva = None

# Obtener manager
rifa_manager = get_rifa_manager()

if not rifa_manager:
    st.error("❌ No se pudo conectar con Google Sheets. Configura las credenciales.")
    st.stop()

# Título principal
st.title("🎲 Rifa Multi-Vendedor")
st.caption("Sistema sincronizado en tiempo real para múltiples vendedores")

# Sidebar - Información del vendedor
st.sidebar.header("👤 Tu Información")
vendedor = st.sidebar.text_input(
    "Tu Nombre:", 
    value=st.session_state.vendedor,
    help="Identifica tus ventas"
)
if vendedor:
    st.session_state.vendedor = vendedor

# Auto-refresh cada 30 segundos
auto_refresh = st.sidebar.checkbox("🔄 Auto-actualizar (30s)", value=True)
if auto_refresh:
    time.sleep(1)  # Pequeña pausa para evitar spam
    if (datetime.now() - st.session_state.ultima_actualizacion).seconds > 30:
        st.session_state.ultima_actualizacion = datetime.now()
        st.rerun()

# Obtener datos actuales
numeros_vendidos = rifa_manager.obtener_numeros_vendidos()
numeros_reservados = rifa_manager.obtener_numeros_reservados()

# Estadísticas
st.sidebar.header("📊 Estadísticas en Vivo")
vendidos_count = len(numeros_vendidos)
reservados_count = len(numeros_reservados)
disponibles_count = 100 - vendidos_count - reservados_count

st.sidebar.metric("✅ Vendidos", vendidos_count)
st.sidebar.metric("⏳ Reservados", reservados_count)
st.sidebar.metric("🟢 Disponibles", disponibles_count)

if vendidos_count > 0:
    porcentaje = (vendidos_count / 100) * 100
    st.sidebar.metric("📈 Progreso", f"{porcentaje:.1f}%")

# Información de reserva actual
if st.session_state.numero_reservado:
    reserva_info = numeros_reservados.get(st.session_state.numero_reservado)
    if reserva_info and reserva_info['vendedor'] == vendedor:
        expira = datetime.fromisoformat(reserva_info['expira_en'])
        tiempo_restante = expira - datetime.now()
        if tiempo_restante.total_seconds() > 0:
            minutos = int(tiempo_restante.total_seconds() // 60)
            segundos = int(tiempo_restante.total_seconds() % 60)
            st.sidebar.warning(f"⏰ Tienes reservado el #{st.session_state.numero_reservado}\nExpira en: {minutos}m {segundos}s")
        else:
            st.session_state.numero_reservado = None

def mostrar_grilla_numeros():
    st.header("🔢 Estado de los Números")
    
    # Botón de actualización manual
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Actualizar", type="secondary"):
            st.rerun()
    
    # Crear la grilla 10x10
    cols = st.columns(10)
    
    for i in range(100):
        numero = i + 1
        col_index = i % 10
        
        with cols[col_index]:
            if numero in numeros_vendidos:
                # Número vendido - rojo
                info = numeros_vendidos[numero]
                st.markdown(
                    f"""<div style='
                        background-color: #ff4444; 
                        color: white; 
                        text-align: center; 
                        padding: 8px; 
                        margin: 2px; 
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 12px;
                    ' title='VENDIDO - {info["comprador"]} ({info["vendedor"]})'>{numero}</div>""", 
                    unsafe_allow_html=True
                )
            elif numero in numeros_reservados:
                # Número reservado - amarillo
                info = numeros_reservados[numero]
                color = "#ffaa00" if info['vendedor'] != vendedor else "#ff8800"
                st.markdown(
                    f"""<div style='
                        background-color: {color}; 
                        color: white; 
                        text-align: center; 
                        padding: 8px; 
                        margin: 2px; 
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 12px;
                    ' title='RESERVADO por {info["vendedor"]}'>{numero}</div>""", 
                    unsafe_allow_html=True
                )
            else:
                # Número disponible - verde
                st.markdown(
                    f"""<div style='
                        background-color: #44ff44; 
                        color: black; 
                        text-align: center; 
                        padding: 8px; 
                        margin: 2px; 
                        border-radius: 5px;
                        font-weight: bold;
                        font-size: 12px;
                    '>{numero}</div>""", 
                    unsafe_allow_html=True
                )

def proceso_venta():
    st.header("💰 Proceso de Venta")
    
    if not vendedor:
        st.warning("⚠️ Ingresa tu nombre en la barra lateral primero.")
        return
    
    # Paso 1: Reservar número
    if not st.session_state.numero_reservado:
        st.subheader("Paso 1: Reservar Número")
        
        numeros_disponibles = []
        for i in range(1, 101):
            if i not in numeros_vendidos and i not in numeros_reservados:
                numeros_disponibles.append(i)
        
        if not numeros_disponibles:
            st.error("🚫 No hay números disponibles")
            return
        
        col1, col2 = st.columns([2, 1])
        with col1:
            numero_elegido = st.selectbox(
                "Elige el número a reservar:",
                numeros_disponibles
            )
        with col2:
            if st.button("🔒 Reservar", type="primary"):
                success, message = rifa_manager.reservar_numero(numero_elegido, vendedor)
                if success:
                    st.session_state.numero_reservado = numero_elegido
                    st.success(f"✅ {message}")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
                    st.rerun()
    
    # Paso 2: Confirmar venta
    else:
        st.subheader(f"Paso 2: Confirmar Venta del Número {st.session_state.numero_reservado}")
        
        with st.form("confirmar_venta"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre_comprador = st.text_input("Nombre del comprador:")
                
            with col2:
                telefono = st.text_input("Teléfono:")
            
            col1, col2 = st.columns(2)
            with col1:
                confirmar = st.form_submit_button("✅ Confirmar Venta", type="primary")
            with col2:
                cancelar = st.form_submit_button("❌ Cancelar Reserva", type="secondary")
            
            if confirmar:
                if nombre_comprador and telefono:
                    success, message = rifa_manager.confirmar_venta(
                        st.session_state.numero_reservado, 
                        nombre_comprador, 
                        telefono, 
                        vendedor
                    )
                    if success:
                        st.success(f"🎉 {message}")
                        st.session_state.numero_reservado = None
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Completa todos los campos")
            
            if cancelar:
                rifa_manager.cancelar_reserva(st.session_state.numero_reservado, vendedor)
                st.session_state.numero_reservado = None
                st.info("Reserva cancelada")
                st.rerun()

def mostrar_ventas():
    st.header("📋 Registro de Ventas")
    
    if not numeros_vendidos:
        st.info("ℹ️ No hay ventas registradas aún.")
        return
    
    # Convertir a DataFrame
    data = []
    for numero, info in numeros_vendidos.items():
        data.append({
            'Número': numero,
            'Comprador': info['comprador'],
            'Teléfono': info['telefono'],
            'Vendedor': info['vendedor'],
            'Fecha': info['fecha_venta']
        })
    
    df = pd.DataFrame(data)
    df = df.sort_values('Número')
    
    # Filtro por vendedor
    col1, col2 = st.columns([2, 1])
    with col1:
        filtro_vendedor = st.selectbox(
            "Filtrar por vendedor:",
            ["Todos"] + list(df['Vendedor'].unique())
        )
    
    if filtro_vendedor != "Todos":
        df_filtrado = df[df['Vendedor'] == filtro_vendedor]
    else:
        df_filtrado = df
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Estadísticas por vendedor
    st.subheader("📊 Ventas por Vendedor")
    ventas_por_vendedor = df.groupby('Vendedor').size().sort_values(ascending=False)
    st.bar_chart(ventas_por_vendedor)

# Layout principal
tab1, tab2, tab3 = st.tabs(["🔢 Números", "💰 Vender", "📋 Ventas"])

with tab1:
    mostrar_grilla_numeros()
    
    # Leyenda
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟢 **Verde:** Disponibles")
    with col2:
        st.markdown("🟡 **Amarillo:** Reservados")
    with col3:
        st.markdown("🔴 **Rojo:** Vendidos")

with tab2:
    proceso_venta()

with tab3:
    mostrar_ventas()

# Footer
st.markdown("---")
st.markdown("*Sistema multi-vendedor sincronizado con Google Sheets*")
st.caption(f"Última actualización: {st.session_state.ultima_actualizacion.strftime('%H:%M:%S')}")