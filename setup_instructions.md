# 🎲 Rifa Multi-Vendedor

Sistema de gestión de rifas para múltiples vendedores con sincronización en tiempo real usando Google Sheets.

## 🚀 Características

- ✅ **Multi-vendedor**: Varios vendedores pueden trabajar simultáneamente
- 🔒 **Sin sobreventa**: Sistema de reservas temporales 
- ⚡ **Tiempo real**: Sincronización automática cada 30 segundos
- 📊 **Estadísticas en vivo**: Estado actualizado de ventas
- 🎯 **Fácil de usar**: Proceso de venta en 2 pasos

## 📋 Configuración Inicial

### 1. Crear Google Sheet
1. Ve a [Google Sheets](https://sheets.google.com)
2. Crea una nueva hoja de cálculo
3. Anota el ID de la hoja (está en la URL): `docs.google.com/spreadsheets/d/[ESTE_ES_EL_ID]/edit`

### 2. Crear Service Account en Google Cloud
1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un nuevo proyecto (o usa uno existente)
3. Habilita las APIs:
   - Google Sheets API
   - Google Drive API
4. Ve a "IAM & Admin" > "Service Accounts"
5. Crea una nueva Service Account
6. Descarga el archivo JSON de credenciales
7. Comparte tu Google Sheet con el email de la Service Account (permisos de Editor)

### 3. Deploy en Streamlit.app

#### Subir código a GitHub:
1. Crea un repositorio en GitHub
2. Sube estos archivos:
   - `app.py` (código principal)
   - `requirements.txt`
   - `README.md`

#### Configurar en Streamlit.app:
1. Ve a [streamlit.app](https://streamlit.app)
2. Conecta tu repositorio de GitHub
3. Ve a "Advanced settings" > "Secrets"
4. Agrega estas variables:

```toml
[gcp_service_account]
type = "service_account"
project_id = "tu-proyecto-id"
private_key_id = "key-id-from-json"
private_key = "-----BEGIN PRIVATE KEY-----\nTU_PRIVATE_KEY_AQUI\n-----END PRIVATE KEY-----\n"
client_email = "service-account@proyecto.iam.gserviceaccount.com"
client_id = "client-id-from-json"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/service-account%40proyecto.iam.gserviceaccount.com"

google_sheet_id = "1ABC123XYZ456789_TU_SHEET_ID_AQUI"
```

## 🎯 Cómo Usar

### Para Vendedores:
1. **Identificarse**: Escribir nombre en la barra lateral
2. **Elegir número**: Seleccionar número disponible (verde)
3. **Reservar**: Click en "Reservar" (número se pone amarillo por 5 minutos)
4. **Completar venta**: Ingresar datos del comprador y confirmar
5. **Listo**: El número se marca como vendido (rojo)

### Estados de Números:
- 🟢 **Verde**: Disponible para reservar
- 🟡 **Amarillo**: Reservado temporalmente
- 🔴 **Rojo**: Vendido definitivamente

## 🔧 Características Técnicas

### Sistema de Reservas
- Cada número se puede reservar por 5 minutos
- Solo el vendedor que reservó puede confirmar la venta
- Las reservas expiradas se limpian automáticamente

### Sincronización
- Auto-actualización cada 30 segundos
- Botón de actualización manual disponible
- Estado compartido en tiempo real entre todos los vendedores

### Datos Almacenados
- **Hoja "ventas"**: Registro permanente de números vendidos
- **Hoja "reservas"**: Reservas temporales con timestamp

## 🚨 Solución de Problemas

### Error de Conexión a Google Sheets
- Verificar que las credenciales estén correctas en Streamlit secrets
- Confirmar que el Service Account tiene acceso al Google Sheet
- Verificar que las APIs estén habilitadas en Google Cloud

### Números "Trabados" en Reserva
- Las reservas se limpian automáticamente después de 5 minutos
- Un vendedor puede cancelar su propia reserva manualmente

### Múltiples Vendedores Ven Diferentes Estados
- Hacer clic en "Actualizar" manualmente
- Verificar conexión a internet
- Las diferencias se sincronizan en máximo 30 segundos

## 📈 Mejoras Futuras Posibles

- [ ] Notificaciones push cuando se vende un número
- [ ] Historial detallado de actividad por vendedor
- [ ] Sistema de comisiones por vendedor
- [ ] Modo offline con sincronización posterior
- [ ] Integración con sistemas de pago

## 📞 Soporte

Si encuentras problemas:
1. Revisa que todos los pasos de configuración estén correctos
2. Verifica las credenciales en Streamlit secrets
3. Confirma que el Google Sheet sea accesible para el Service Account

---

*Desarrollado para gestión eficiente de rifas multi-vendedor*