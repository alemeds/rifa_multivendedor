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

def get_available_numbers(df, total_numbers=1000):
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
            'total_disponibles': 1000,
            'monto_total': 0,
            'ventas_por_vendedor': {}
        }
    
    sold_df = df[df['estado'] == 'vendido']
    
    summary = {
        'total_vendidos': len(sold_df),
        'total_disponibles': 1000 - len(sold_df),
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

    .manual-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .step-box {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #51cf66;
    }
    
    .warning-box {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #ffc107;
    }
    
    .tip-box {
        background: #d1ecf1;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #17a2b8;
    }
    </style>
    """, unsafe_allow_html=True)

def display_number_grid(available_numbers, sold_numbers, total_numbers=1000):
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

def show_user_manual():
    """Muestra el manual de usuario completo"""
    st.markdown("""
    <div class="main-header">
        <h1>📖 Manual de Usuario</h1>
        <p>Guía completa para usar el Sistema de Rifa Multivendedor</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Índice de contenidos
    st.markdown("""
    <div class="manual-section">
        <h3>📋 Índice de Contenidos</h3>
        <ul>
            <li><a href="#overview">1. Descripción General del Sistema</a></li>
            <li><a href="#navigation">2. Navegación por el Sistema</a></li>
            <li><a href="#inicio">3. Página de Inicio</a></li>
            <li><a href="#comprar">4. Comprar Número</a></li>
            <li><a href="#vendedor">5. Panel del Vendedor</a></li>
            <li><a href="#admin">6. Panel de Administración</a></li>
            <li><a href="#troubleshooting">7. Solución de Problemas</a></li>
            <li><a href="#tips">8. Consejos y Mejores Prácticas</a></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Descripción General
    st.markdown('<a id="overview"></a>', unsafe_allow_html=True)
    st.markdown("## 1. 🎯 Descripción General del Sistema")
    
    st.markdown("""
    <div class="manual-section">
        <p>El Sistema de Rifa Multivendedor es una aplicación web diseñada para gestionar rifas de manera eficiente y transparente. Permite:</p>
        <ul>
            <li><strong>Venta de números:</strong> Múltiples vendedores pueden vender números de rifa</li>
            <li><strong>Seguimiento en tiempo real:</strong> Estado actualizado de números vendidos y disponibles</li>
            <li><strong>Gestión de vendedores:</strong> Control individual de ventas por vendedor</li>
            <li><strong>Administración centralizada:</strong> Panel completo para supervisión y reportes</li>
            <li><strong>Sorteo automático:</strong> Funcionalidad para realizar el sorteo de manera aleatoria</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Especificaciones técnicas
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="tip-box">
            <h4>🎟️ Especificaciones de la Rifa</h4>
            <ul>
                <li><strong>Total de números:</strong> 1000 (del 1 al 1000)</li>
                <li><strong>Precio por número:</strong> $5,000</li>
                <li><strong>Recaudación máxima:</strong> $2,500,000</li>
                <li><strong>Comisión vendedores:</strong> 10%</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="tip-box">
            <h4>👥 Tipos de Usuario</h4>
            <ul>
                <li><strong>Compradores:</strong> Pueden adquirir números</li>
                <li><strong>Vendedores:</strong> Gestionan sus ventas</li>
                <li><strong>Administradores:</strong> Control total del sistema</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # 2. Navegación
    st.markdown('<a id="navigation"></a>', unsafe_allow_html=True)
    st.markdown("## 2. 🧭 Navegación por el Sistema")
    
    st.markdown("""
    <div class="manual-section">
        <p>El sistema está organizado en 5 secciones principales accesibles desde el menú lateral izquierdo:</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="step-box">
            <h4>🏠 Inicio</h4>
            <p>Vista general del estado de la rifa, estadísticas principales y grilla visual de números.</p>
        </div>
        
        <div class="step-box">
            <h4>🛒 Comprar Número</h4>
            <p>Formulario para que los clientes adquieran números de la rifa.</p>
        </div>
        
        <div class="step-box">
            <h4>📖 Manual de Usuario</h4>
            <p>Esta sección con toda la documentación del sistema.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="step-box">
            <h4>👥 Panel Vendedor</h4>
            <p>Área de trabajo para vendedores: ver sus ventas, estadísticas y agregar ventas manuales.</p>
        </div>
        
        <div class="step-box">
            <h4>📊 Administración</h4>
            <p>Panel completo para administradores: reportes, datos completos y herramientas administrativas.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 3. Página de Inicio
    st.markdown('<a id="inicio"></a>', unsafe_allow_html=True)
    st.markdown("## 3. 🏠 Página de Inicio")
    
    st.markdown("""
    <div class="manual-section">
        <p>La página de inicio es el centro de información de la rifa. Aquí encontrarás:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas principales
    st.markdown("### 📊 Métricas Principales")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="tip-box">
            <h5>📊 Números Vendidos</h5>
            <p>Cantidad total de números ya vendidos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="tip-box">
            <h5>✅ Números Disponibles</h5>
            <p>Cantidad de números aún disponibles para venta</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="tip-box">
            <h5>💰 Recaudación Total</h5>
            <p>Monto total recaudado hasta el momento</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="tip-box">
            <h5>📈 Progreso</h5>
            <p>Porcentaje de avance en la venta de números</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Grilla de números
    st.markdown("### 🎯 Grilla de Números")
    st.markdown("""
    <div class="step-box">
        <h4>¿Cómo interpretar la grilla?</h4>
        <ul>
            <li><span style="background:#ff6b6b; color:white; padding:2px 8px; border-radius:3px;">Números Rojos</span>: Ya están vendidos</li>
            <li><span style="background:#51cf66; color:white; padding:2px 8px; border-radius:3px;">Números Verdes</span>: Disponibles para compra</li>
        </ul>
        <p>La grilla muestra los 1000 números organizados en filas de 10 números cada una.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 4. Comprar Número
    st.markdown('<a id="comprar"></a>', unsafe_allow_html=True)
    st.markdown("## 4. 🛒 Comprar Número")
    
    st.markdown("""
    <div class="manual-section">
        <p>Esta sección permite a los clientes adquirir números de la rifa de manera sencilla y segura.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📝 Proceso de Compra")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="step-box">
            <h4>Paso 1: Información del Comprador</h4>
            <ul>
                <li><strong>Nombre completo*:</strong> Nombre y apellido del comprador</li>
                <li><strong>Teléfono*:</strong> Número de contacto (requerido para comunicación)</li>
                <li><strong>Email:</strong> Correo electrónico (opcional pero recomendado)</li>
            </ul>
            <p><em>Los campos marcados con * son obligatorios</em></p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="step-box">
            <h4>Paso 2: Detalles de la Compra</h4>
            <ul>
                <li><strong>Vendedor*:</strong> Seleccionar el vendedor que realiza la venta</li>
                <li><strong>Número a comprar*:</strong> Elegir de la lista de números disponibles</li>
                <li><strong>Monto:</strong> Precio del número (default $5,000)</li>
                <li><strong>Observaciones:</strong> Información adicional (opcional)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-box">
        <h4>⚠️ Importante</h4>
        <ul>
            <li>Una vez confirmada la compra, el número quedará inmediatamente marcado como vendido</li>
            <li>No se pueden realizar cambios después de confirmar la compra</li>
            <li>El sistema mostrará una confirmación con efectos visuales (globos) al completar la venta</li>
            <li>Si hay un error, contacta al administrador inmediatamente</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 5. Panel del Vendedor
    st.markdown('<a id="vendedor"></a>', unsafe_allow_html=True)
    st.markdown("## 5. 👥 Panel del Vendedor")
    
    st.markdown("""
    <div class="manual-section">
        <p>El panel del vendedor es el área de trabajo para quienes se encargan de vender números. Incluye estadísticas personales y herramientas de gestión.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Estadísticas del Vendedor")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="tip-box">
            <h5>🎯 Números Vendidos</h5>
            <p>Cantidad total de números vendidos por el vendedor seleccionado</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="tip-box">
            <h5>💰 Total Recaudado</h5>
            <p>Monto total generado por las ventas del vendedor</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="tip-box">
            <h5>💼 Comisión (10%)</h5>
            <p>Comisión ganada por el vendedor (10% del total recaudado)</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📋 Funcionalidades Principales")
    
    st.markdown("""
    <div class="step-box">
        <h4>1. Filtro por Vendedor</h4>
        <p>Usa el selector para ver las estadísticas y ventas de un vendedor específico o todos los vendedores.</p>
    </div>
    
    <div class="step-box">
        <h4>2. Registro de Ventas</h4>
        <p>Tabla completa con todas las ventas realizadas por el vendedor, incluyendo:</p>
        <ul>
            <li>Fecha y hora de la venta</li>
            <li>Número vendido</li>
            <li>Información del comprador</li>
            <li>Monto y estado</li>
            <li>Observaciones</li>
        </ul>
    </div>
    
    <div class="step-box">
        <h4>3. Agregar Venta Manual</h4>
        <p>Expandir la sección "➕ Agregar Venta Manual" para registrar ventas realizadas fuera del sistema:</p>
        <ul>
            <li>Completa todos los campos requeridos</li>
            <li>Selecciona un número disponible</li>
            <li>El sistema marcará automáticamente la venta como "Venta manual"</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-box">
        <h4>⚠️ Importante para Vendedores</h4>
        <ul>
            <li>Siempre verifica que el número esté disponible antes de prometerlo a un cliente</li>
            <li>Registra las ventas inmediatamente para evitar números duplicados</li>
            <li>Mantén actualizada la información de contacto de los compradores</li>
            <li>Las comisiones se calculan automáticamente basadas en el total recaudado</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 6. Panel de Administración
    st.markdown('<a id="admin"></a>', unsafe_allow_html=True)
    st.markdown("## 6. 📊 Panel de Administración")
    
    st.markdown("""
    <div class="manual-section">
        <p>El panel de administración es el centro de control completo del sistema. Solo usuarios autorizados deben tener acceso a esta sección.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📈 Métricas Avanzadas")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="tip-box">
            <h5>📊 Total Vendidos</h5>
            <p>Muestra comparativo vs objetivo</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="tip-box">
            <h5>💰 Recaudación</h5>
            <p>Monto total recaudado</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="tip-box">
            <h5>⚡ Eficiencia</h5>
            <p>Porcentaje de números vendidos</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="tip-box">
            <h5>👥 Vendedores Activos</h5>
            <p>Cantidad de vendedores con ventas</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🔧 Herramientas Administrativas")
    
    st.markdown("""
    <div class="step-box">
        <h4>1. Filtros Avanzados</h4>
        <ul>
            <li><strong>Filtrar por fecha:</strong> Ver ventas de una fecha específica</li>
            <li><strong>Filtrar por vendedor:</strong> Análisis por vendedor individual</li>
            <li><strong>Filtrar por estado:</strong> Ver solo ventas vendidas, reservadas o canceladas</li>
        </ul>
    </div>
    
    <div class="step-box">
        <h4>2. Exportación de Datos</h4>
        <ul>
            <li>Botón "📥 Descargar CSV" para exportar reportes</li>
            <li>El archivo incluye todos los datos filtrados</li>
            <li>Nombre automático con fecha de generación</li>
        </ul>
    </div>
    
    <div class="step-box">
        <h4>3. Herramientas de Sorteo</h4>
        <ul>
            <li><strong>🎲 Realizar Sorteo:</strong> Selecciona aleatoriamente un número ganador</li>
            <li>Solo considera números efectivamente vendidos</li>
            <li>Muestra información completa del ganador</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="warning-box">
        <h4>⚠️ Funciones Críticas</h4>
        <ul>
            <li><strong>🗑️ Limpiar Datos:</strong> Función para resetear todo el sistema (usar con extrema precaución)</li>
            <li>Esta función eliminaría TODOS los datos de ventas</li>
            <li>Solo debe usarse con autorización explícita y respaldo previo</li>
            <li>Actualmente muestra solo advertencia (requiere implementación adicional)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 7. Solución de Problemas
    st.markdown('<a id="troubleshooting"></a>', unsafe_allow_html=True)
    st.markdown("## 7. 🛠️ Solución de Problemas")
    
    st.markdown("### ❌ Problemas Comunes y Soluciones")
    
    st.markdown("""
    <div class="step-box">
        <h4>Error: "No se pudo establecer conexión con Google Sheets"</h4>
        <ul>
            <li><strong>Causa:</strong> Problema de configuración de credenciales</li>
            <li><strong>Solución:</strong> Contactar al administrador técnico</li>
            <li><strong>Usuario:</strong> Actualizar la página y intentar nuevamente</li>
        </ul>
    </div>
    
    <div class="step-box">
        <h4>Error: "Error al obtener datos"</h4>
        <ul>
            <li><strong>Causa:</strong> Problema de conectividad o permisos</li>
            <li><strong>Solución:</strong> Esperar unos minutos y recargar la página</li>
            <li><strong>Si persiste:</strong> Reportar al administrador</li>
        </ul>
    </div>
    
    <div class="step-box">
        <h4>Error: "Error al guardar venta"</h4>
        <ul>
            <li><strong>Causa:</strong> Problema al escribir en Google Sheets</li>
            <li><strong>Solución inmediata:</strong> Verificar que todos los campos estén completados correctamente</li>
            <li><strong>Si persiste:</strong> Usar "Agregar Venta Manual" en el Panel del Vendedor</li>
        </ul>
    </div>
    
    <div class="step-box">
        <h4>El número que quiero no aparece disponible</h4>
        <ul>
            <li><strong>Verificar:</strong> Que el número no esté en la grilla roja (vendido)</li>
            <li><strong>Actualizar:</strong> Recargar la página para obtener datos más recientes</li>
            <li><strong>Alternativa:</strong> Elegir otro número disponible</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔄 ¿Cuándo Actualizar la Página?")
    
    st.markdown("""
    <div class="tip-box">
        <h4>Actualización Automática vs Manual</h4>
        <ul>
            <li><strong>Automática:</strong> El sistema se actualiza automáticamente después de cada venta exitosa</li>
            <li><strong>Manual:</strong> Usa F5 o el botón de actualizar del navegador si:</li>
            <ul>
                <li>Los datos parecen desactualizados</li>
                <li>Han pasado varios minutos sin actividad</li>
                <li>Hay inconsistencias en la información mostrada</li>
            </ul>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # 8. Consejos y Mejores Prácticas
    st.markdown('<a id="tips"></a>', unsafe_allow_html=True)
    st.markdown("## 8. 💡 Consejos y Mejores Prácticas")
    
    st.markdown("### 🎯 Para Compradores")
    st.markdown("""
    <div class="tip-box">
        <ul>
            <li><strong>Números populares:</strong> Los números bajos (1-100) y especiales (100, 200, etc.) se agotan rápido</li>
            <li><strong>Información completa:</strong> Proporciona teléfono y email válidos para contacto</li>
            <li><strong>Confirmación:</strong> Guarda la información de tu compra (número y vendedor)</li>
            <li><strong>Verificación:</strong> Consulta el estado en la grilla principal después de comprar</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 👥 Para Vendedores")
    st.markdown("""
    <div class="tip-box">
        <ul>
            <li><strong>Verificación previa:</strong> Siempre confirma disponibilidad antes de prometer un número</li>
            <li><strong>Registro inmediato:</strong> Registra las ventas tan pronto como recibas el pago</li>
            <li><strong>Información completa:</strong> Solicita datos completos del comprador</li>
            <li><strong>Seguimiento:</strong> Revisa tus estadísticas regularmente en el Panel del Vendedor</li>
            <li><strong>Ventas manuales:</strong> Usa la función de venta manual para ventas realizadas fuera del sistema</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Para Administradores")
    st.markdown("""
    <div class="tip-box">
        <ul>
            <li><strong>Monitoreo regular:</strong> Revisa las estadísticas diariamente</li>
            <li><strong>Respaldos:</strong> Exporta datos regularmente como respaldo</li>
            <li><strong>Comunicación:</strong> Mantén informados a los vendedores sobre el progreso</li>
            <li><strong>Sorteo:</strong> Realiza el sorteo solo cuando se hayan vendido todos los números o en la fecha programada</li>
            <li><strong>Resolución de conflictos:</strong> Actúa rápidamente ante números duplicados o problemas técnicos</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔐 Seguridad y Privacidad")
    st.markdown("""
    <div class="warning-box">
        <h4>Protección de Datos</h4>
        <ul>
            <li>Los datos de compradores se almacenan de forma segura en Google Sheets</li>
            <li>No compartir credenciales de acceso</li>
            <li>Reportar inmediatamente cualquier actividad sospechosa</li>
            <li>Mantener confidencial la información de los compradores</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer del manual
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; margin-top: 2rem;">
        <p><strong>📖 Manual de Usuario - Sistema de Rifa Multivendedor</strong></p>
        <p>Versión 1.0 | Para soporte técnico, contacta al administrador del sistema</p>
    </div>
    """, unsafe_allow_html=True)

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
        ["🏠 Inicio", "🛒 Comprar Número", "📖 Manual de Usuario", "👥 Panel Vendedor", "📊 Administración"]
    )
    
    # Mostrar manual de usuario
    if page == "📖 Manual de Usuario":
        show_user_manual()
        return
    
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
            progress = summary['total_vendidos'] / 1000 * 100
            st.metric("📈 Progreso", f"{progress:.1f}%")
        
        # Mostrar grilla de números
        display_number_grid(available_numbers, sold_numbers)
        
        # Información adicional
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Información de la Rifa")
            st.write("- **Total de números:** 1000")
            st.write("- **Precio por número:** $5,000")
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
                vendedor = st.selectbox("Vendedor *", ["ENRIQUE CARDENAS",
                                                       "MARCELA RAGGI", 
                                                       "STELLA",
                                                       "ANTONIO MARTINEZ", 
                                                       "ROSA CLOSS", 
                                                       "MARIANA PRADO", 
                                                       "CARO CROSTA", 
                                                       "SANDRA DASSO", 
                                                       "SERGIO", 
                                                       "FERNANDO", 
                                                       "MARTIN",
                                                       "Otro"])
                if vendedor == "Otro":
                    vendedor = st.text_input("Nombre del vendedor")
                
                numero_seleccionado = st.selectbox("Número a comprar *", available_numbers)
                monto = st.number_input("Monto ($)", value=2500, min_value=1000)
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
                                     ["Todos"] + list(summary['ventas_por_vendedor'].keys()) + ["ENRIQUE CARDENAS", "MARCELA RAGGI", "STELLA"])
        
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
                    monto_manual = st.number_input("Monto", value=2500)
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
            efficiency = (summary['total_vendidos'] / 1000) * 100
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
