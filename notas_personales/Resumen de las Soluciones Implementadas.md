He identificado y corregido varios problemas críticos en tu sistema:

1. Error Principal: Puerto Incorrecto

❌ Problema: El frontend intentaba conectarse al puerto 8000 pero el servidor está en 8001
✅ Solución: Actualizado useWebSocket.ts para usar ws://localhost:8001/ws

2. Método Inexistente en API

❌ Problema: binance_websocket.py llamaba a broadcast_json() que no existe
✅ Solución: Cambiado a broadcast() que es el método correcto

3. Mejoras en la Estabilidad del WebSocket

✅ Añadido mejor manejo de reconexión con backoff exponencial
✅ Configurados timeouts y ping/pong para mantener la conexión viva
✅ Añadido manejo de heartbeat en el frontend

4. Herramientas de Diagnóstico
He creado 3 scripts útiles:

restart_system.bat - Reinicia rápidamente el sistema completo
diagnose_system.py - Diagnostica problemas de conexión
test_websocket.py - Prueba específicamente el WebSocket

📋 Pasos para Solucionar el Problema

Paso 1: Detener todos los servicios
bash# Cierra todas las ventanas de terminal o ejecuta:
taskkill /F /IM python.exe
taskkill /F /IM node.exe

Paso 2: Reiniciar el sistema
Ejecuta el script de reinicio:
bashcd C:\Users\zamor\Bot_Arbitraje2105
restart_system.bat

Paso 3: Verificar el diagnóstico
En una nueva terminal, ejecuta:
bashcd C:\Users\zamor\Bot_Arbitraje2105
python diagnose_system.py

Paso 4: Verificar en el navegador
Abre Chrome/Edge en http://localhost:5173
Abre las DevTools (F12)
Ve a la pestaña Console

Deberías ver mensajes como:

"🔗 WebSocket connected to enhanced server"
"✅ Connected to enhanced trading server"
"📊 Market Data: BTCUSDT = $..."

🔧 Si Aún Hay Problemas
Opción A: Prueba manual del WebSocket
bashcd C:\Users\zamor\Bot_Arbitraje2105
python test_websocket.py

Opción B: Verificar logs
bash# Ver logs del backend
type logs\production_server.log

# Ver últimas líneas
powershell -command "Get-Content logs\production_server.log -Tail 50"
Opción C: Limpiar y reconstruir el frontend
bashcd C:\Users\zamor\Bot_Arbitraje2105\frontend
npm install
npm run dev

🚀 Arquitectura Mejorada
El sistema ahora tiene:

Reconexión automática con backoff exponencial
Heartbeat bidireccional para mantener conexiones vivas
Mejor logging para debugging
Manejo robusto de errores en toda la cadena

Los cambios principales garantizan que:

El frontend se conecta al puerto correcto (8001)
Los métodos de broadcast son compatibles
Las reconexiones son más inteligentes y estables
Los heartbeats mantienen la conexión activa

¡El sistema debería funcionar correctamente ahora! 🎉