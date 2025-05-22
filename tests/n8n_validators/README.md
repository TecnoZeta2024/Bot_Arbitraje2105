# Validadores de Nodos n8n - Bot de Arbitraje Triangular

Este directorio contiene validadores para los nodos de n8n utilizados en el Bot de Arbitraje Triangular.

## Descripción

Los validadores permiten verificar el correcto funcionamiento de los nodos críticos en el flujo de trabajo de n8n, incluyendo:

1. **Nodo "Evaluar Recomendación IA"**: Valida que el nodo procese correctamente los diferentes tipos de recomendación (PROCEDER, PRECAUCIÓN, DESCARTAR).

2. **Nodo "Procesar Decisión Usuario"**: Verifica que el nodo maneje correctamente las decisiones del usuario (Si/No).

3. **Nodos de Supabase**: Valida la estructura de las tablas en Supabase y permite crearlas si no existen.

## Requisitos Previos

- n8n debe estar ejecutándose localmente en el puerto 5678
- El flujo de trabajo "Bot Arbitraje triangular" debe estar importado y activado en n8n
- La configuración de Supabase debe estar correctamente configurada en el archivo `.env`

## Uso

### Mediante Menú Interactivo

```bash
python main.py
```

Este comando muestra un menú interactivo que permite seleccionar qué validaciones ejecutar.

### Mediante Argumentos de Línea de Comandos

```bash
# Ejecutar todas las validaciones
python main.py --all

# Validar solo nodo de recomendación
python main.py --recomendacion

# Validar solo nodo de decisión
python main.py --decision

# Validar solo tablas Supabase
python main.py --supabase
```

## Validadores Individuales

También se pueden ejecutar los validadores individualmente:

### Validar Nodo "Evaluar Recomendación IA"

```bash
python validar_recomendacion_ia.py
```

Para probar un tipo específico de recomendación:

```bash
python validar_recomendacion_ia.py --tipo PROCEDER
python validar_recomendacion_ia.py --tipo PRECAUCION
python validar_recomendacion_ia.py --tipo DESCARTAR
```

### Validar Nodo "Procesar Decisión Usuario"

```bash
python validar_decision_usuario.py
```

Para probar una decisión específica:

```bash
python validar_decision_usuario.py --decision Si
python validar_decision_usuario.py --decision No
```

### Validar Tablas Supabase

```bash
python validar_supabase.py
```

Este script verifica la existencia de las tablas en Supabase y permite crearlas si no existen, así como insertar datos de prueba.

## Estructura de Archivos

- `main.py`: Script principal para ejecutar todos los validadores.
- `validar_recomendacion_ia.py`: Validador para el nodo "Evaluar Recomendación IA".
- `validar_decision_usuario.py`: Validador para el nodo "Procesar Decisión Usuario".
- `validar_supabase.py`: Validador para las tablas de Supabase.

## Resultados

Los resultados de las validaciones se muestran en la consola y se registran en el archivo de log correspondiente en el directorio `logs/`.

## Consideraciones

- Los validadores envían datos de prueba a través de los webhooks de n8n, por lo que es importante asegurarse de que estén correctamente configurados.
- Si n8n no está ejecutándose en el puerto estándar (5678), es necesario actualizar la configuración en `src/utils/config.py`.
- Para garantizar la consistencia de las pruebas, se recomienda ejecutar los validadores cuando no haya otros procesos interactuando con n8n o Supabase.
