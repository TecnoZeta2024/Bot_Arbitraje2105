# Reglas de Validación de Negocio para Datos Normalizados

Este documento describe las reglas de negocio que los datos normalizados deben cumplir para ser considerados válidos dentro del sistema de arbitraje. Estas reglas aseguran la integridad y la coherencia de los datos antes de ser utilizados por las capas de dominio y aplicación.

## 1. Validación de Precios

*   **Regla:** Todos los valores de precio (`price`) deben ser estrictamente mayores que cero.
*   **Justificación:** Un precio de cero o negativo no tiene sentido en el contexto de operaciones de mercado y podría indicar un error en la fuente de datos o en el proceso de normalización.
*   **Ejemplo Válido:** `price = 0.0001`, `price = 100.50`
*   **Ejemplo Inválido:** `price = 0`, `price = -5.0`

## 2. Validación de Cantidades

*   **Regla:** Todos los valores de cantidad (`amount`, `volume`) deben ser estrictamente mayores que cero.
*   **Justificación:** Una cantidad de cero o negativa no es operativa y podría llevar a cálculos incorrectos o a la omisión de oportunidades válidas.
*   **Ejemplo Válido:** `amount = 0.001`, `amount = 10.0`
*   **Ejemplo Inválido:** `amount = 0`, `amount = -2.5`

## 3. Validación de Rangos Específicos (a definir)

*   **Regla:** Ciertos campos numéricos pueden requerir validación contra rangos mínimos y máximos predefinidos, basados en las características del mercado o los requisitos de la estrategia.
*   **Justificación:** Prevenir valores atípicos o erróneos que puedan distorsionar el análisis o la ejecución de operaciones.
*   **Ejemplos Potenciales:**
    *   `spread_percentage`: Debe estar dentro de un rango razonable (ej. 0.01% a 5%).
    *   `timestamp`: Debe ser un valor de tiempo válido y no estar en el futuro.

## 4. Integridad de Datos Estructurales

*   **Regla:** Los objetos de datos normalizados deben contener todos los campos obligatorios definidos en sus respectivos esquemas (e.g., `symbol`, `exchange`, `timestamp`, `bid_price`, `ask_price`, `bid_quantity`, `ask_quantity`).
*   **Justificación:** Asegurar que la información esencial para el procesamiento posterior esté siempre presente.

## 5. Consistencia de Tipos de Datos

*   **Regla:** Todos los campos deben adherirse a sus tipos de datos esperados (ej. `Decimal` para valores monetarios y cantidades, `str` para símbolos, `int` o `float` para timestamps si no se usa `datetime`).
*   **Justificación:** Evitar errores de tipo en cálculos y operaciones posteriores.

---
**Nota:** Estas reglas son un punto de partida y pueden expandirse o ajustarse a medida que se identifiquen nuevas necesidades de negocio o se refinen las estrategias de arbitraje.
