# Pruebas del Bot de Arbitraje Triangular

Este directorio contiene pruebas unitarias, de integración y de sistema para el Bot de Arbitraje Triangular.

## Estructura

```
tests/
├── n8n_validators/              # Validadores para nodos de n8n
│   ├── main.py                  # Script principal para validadores
│   ├── validar_recomendacion_ia.py  # Validador para nodo "Evaluar Recomendación IA" 
│   ├── validar_decision_usuario.py  # Validador para nodo "Procesar Decisión Usuario"
│   └── validar_supabase.py      # Validador para tablas Supabase
├── test_integracion_n8n.py      # Prueba de integración completa del flujo n8n
└── README.md                    # Este archivo
```

## Pruebas Disponibles

### Validadores de Nodos n8n

Herramientas para validar el correcto funcionamiento de los nodos críticos en el flujo de trabajo n8n.

```bash
# Ejecutar todos los validadores de manera interactiva
cd n8n_validators
python main.py

# Ejecutar validadores específicos
python main.py --recomendacion
python main.py --decision
python main.py --supabase
```

Ver [n8n_validators/README.md](./n8n_validators/README.md) para más detalles.

### Prueba de Integración Completa

Esta prueba simula el flujo completo del sistema, desde la detección de una oportunidad hasta la ejecución y el registro del resultado.

```bash
# Asegúrese de que la API Python y n8n estén activos
python ../main.py --mode api  # En una terminal separada
npx n8n start  # En otra terminal separada

# Ejecutar la prueba de integración
python test_integracion_n8n.py
```

## Requisitos

- Python 3.9+
- n8n v1.0.0+
- API del Bot de Arbitraje Triangular activa
- Conexión a Supabase configurada
- Todas las dependencias instaladas (`pip install -r ../requirements.txt`)

## Ejecución de Todas las Pruebas

Para ejecutar todas las pruebas unitarias del proyecto:

```bash
pytest
```

Para ejecutar las pruebas de integración:

```bash
python test_integracion_n8n.py
```

## Consideraciones

- Las pruebas de integración requieren que todos los componentes del sistema estén funcionando.
- Algunas pruebas pueden interactuar con servicios externos (Binance, Telegram), utilice bancos de pruebas o mocks cuando sea posible.
- El modo de prueba (`--test`) en `main.py` puede ser útil para evitar bucles continuos durante las pruebas.
