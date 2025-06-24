# 🎟️ Rifa Multivendedor

Sistema completo de gestión de rifas con múltiples vendedores desarrollado en Streamlit y Google Sheets.

## 🚀 Características

- **Gestión de Rifas**: Sistema completo para rifas de 100 números
- **Multivendedor**: Soporte para múltiples vendedores con seguimiento individual
- **Tiempo Real**: Actualización automática desde Google Sheets
- **Panel Administrativo**: Control total de ventas y estadísticas
- **Interfaz Intuitiva**: Diseño moderno y fácil de usar
- **Exportación de Datos**: Descarga de reportes en CSV

## 📋 Funcionalidades

### Para Compradores
- Visualización de números disponibles
- Compra fácil con formulario interactivo
- Confirmación inmediata de compra

### Para Vendedores
- Panel personalizado por vendedor
- Registro manual de ventas
- Estadísticas de comisiones
- Historial de ventas

### Para Administradores
- Dashboard completo con métricas
- Gestión de todos los vendedores
- Herramientas de sorteo
- Exportación de datos
- Filtros avanzados

## 🛠️ Instalación y Configuración

### 1. Configurar Google Sheets

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google Sheets
4. Crea credenciales de Service Account
5. Descarga el archivo JSON de credenciales

### 2. Preparar Google Sheets

1. Crea una nueva hoja de cálculo en Google Sheets
2. Compártela con el email del service account (con permisos de editor)
3. Copia el ID de la hoja (está en la URL)

### 3. Configuración Local

```bash
# Clonar el repositorio
git clone https://github.com/alemeds/rifa_multivendedor.git
cd rifa_multivendedor

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configurar Secrets

Crea el archivo `.streamlit/secrets.toml` con:

```toml
# Google Sheets Configuration
GOOGLE_SHEET_ID = "tu-sheet-id-aqui"

# Google Cloud Service Account Credentials
[gcp_service_account]
type = "service_account"
project_id = "tu-proyecto"
private_key_id = "tu-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\ntu-private-key-aqui\n-----END PRIVATE KEY-----"
client_email = "tu-service-account@tu-proyecto.iam.gserviceaccount.com"
client_id = "tu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/tu-service-account%40tu-proyecto.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

### 5. Ejecutar Localmente

```bash
streamlit run app.py
```

## 🌐 Despliegue en Streamlit Cloud

### 1. Preparar Repositorio

1. Sube tu código a GitHub
2. Asegúrate de NO incluir el archivo `secrets.toml` (debe estar en `.gitignore`)

### 2. Configurar en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu repositorio de GitHub
3. En Settings → Secrets, pega el contenido de tu `secrets.toml`
4. Despliega la aplicación

### 3. Configuración del .gitignore

```
.streamlit/
__pycache__/
*.pyc
.env
.venv/
venv/
```

## 📊 Estructura de Datos en Google Sheets

La aplicación creará automáticamente una hoja llamada "ventas" con las siguientes columnas:

| Columna | Descripción |
|---------|-------------|
| fecha | Fecha y hora de la venta |
| vendedor | Nombre del vendedor |
| numero | Número de rifa vendido |
| nombre_comprador | Nombre del comprador |
| telefono | Teléfono del comprador |
| email | Email del comprador |
| monto | Monto de la venta |
| estado | Estado (vendido, reservado, cancelado) |
| observaciones | Notas adicionales |

## 🔧 Personalización

### Modificar Precio Base
Cambia el valor por defecto en la línea:
```python
monto = st.number_input("Monto ($)", value=10000, min_value=1000)
```

### Cambiar Cantidad de Números
Modifica la variable en:
```python
def get_available_numbers(df, total_numbers=100):
```

### Agregar Vendedores
Edita la lista en:
```python
vendedor = st.selectbox("Vendedor *", ["Vendedor 1", "Vendedor 2", "Vendedor 3", "Otro"])
```

## 🛡️ Seguridad

- **NUNCA** subas el archivo `secrets.toml` a GitHub
- Usa siempre Service Accounts para la autenticación
- Revisa regularmente los permisos de acceso a tu Google Sheet
- Mantén actualizadas las dependencias

## 🆘 Solución de Problemas

### Error: "Invalid regular expression"
- Verifica que las comillas en `private_key` estén correctamente formateadas
- No uses comillas triples `"""` en el archivo secrets
- Asegúrate de que no haya espacios extra

### Error de Conexión a Google Sheets
- Verifica que la hoja esté compartida con el service account
- Revisa que el GOOGLE_SHEET_ID sea correcto
- Confirma que las APIs estén habilitadas

### La aplicación se reinicia constantemente
- Revisa los logs en Streamlit Cloud
- Verifica que todas las dependencias estén en requirements.txt
- Asegúrate de que no hay errores en la configuración

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Si tienes problemas o preguntas:

1. Revisa la sección de solución de problemas
2. Busca en los [Issues](https://github.com/alemeds/rifa_multivendedor/issues) existentes
3. Crea un nuevo Issue si es necesario

---

**¡Desarrollado con ❤️ para facilitar la gestión de rifas!**
