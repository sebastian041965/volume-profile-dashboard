# 📊 Volume Profile Dashboard

Esta app web interactiva permite visualizar el perfil de volumen en tiempo real para criptomonedas (Binance) y pares de divisas (Forex vía Yahoo Finance). Incluye trazado técnico, dibujo libre editable, exportación e importación de anotaciones, y autenticación por usuario con sesión limitada.

## ✨ Funcionalidades

- Perfil de volumen con VPOC, soporte y resistencia
- Trazado técnico entre precios con líneas personalizadas
- Dibujo libre editable (mover, clonar, cambiar color y grosor)
- Exportación de anotaciones como JSON o CSV
- Importación de anotaciones guardadas
- Autenticación por usuario con sesión de 30 minutos
- Interfaz organizada en pestañas

## 🚀 Despliegue en Streamlit Cloud

1. Sube este repositorio a tu cuenta de GitHub.
2. Ve a [streamlit.io/cloud](https://streamlit.io/cloud) e inicia sesión.
3. Haz clic en “New app”.
4. Selecciona este repositorio.
5. Usa `volume_profile_app.py` como archivo principal.
6. ¡Tu app estará online!

## 🛠️ Requisitos

- Python 3.8+
- Las dependencias están en `requirements.txt`

## 🔐 Acceso

Usuarios definidos por defecto:

| Usuario    | Contraseña   |
|------------|--------------|
| sebastian  | clave123     |
| analista   | trading2025  |
| admin      | adminpass    |

La sesión expira automáticamente tras 30 minutos. Puedes cerrar sesión manualmente desde la barra lateral.

---

¿Quieres que el README incluya capturas de pantalla, tu logo, o instrucciones para desplegarlo en tu propio dominio? Puedo ayudarte a personalizarlo aún más.
