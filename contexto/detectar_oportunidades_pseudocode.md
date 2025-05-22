# Módulo para detectar oportunidades de arbitraje triangular.

# Función: save_market_data_to_cache
# Descripción: Guarda los datos de mercado en caché, manteniendo solo los 5 archivos más recientes.
# Parámetros:
#   symbols: Lista de símbolos de trading.
#   tickers: Diccionario de tickers (símbolo: precio).
#   cache_dir: Directorio para los archivos de caché (por defecto: "./cache").
# Retorna:
#   Ruta del archivo de caché creado.
Función save_market_data_to_cache(symbols, tickers, cache_dir):
  Crear directorio cache_dir si no existe.
  Generar nombre de archivo con timestamp: "market_data_YYYYMMDD_HHMMSS.json".
  Construir ruta completa del archivo.
  Crear diccionario de datos con symbols, tickers y timestamp.
  Guardar datos en el archivo JSON.
  Listar todos los archivos "market_data_*.json" en cache_dir.
  Ordenar archivos por nombre (timestamp).
  Mientras haya más de 5 archivos:
    Eliminar el archivo más antiguo.
  Registrar que los datos fueron guardados en caché.
  Retornar la ruta del archivo creado.

# Función: load_market_data_from_cache
# Descripción: Carga los datos de mercado más recientes del caché.
# Parámetros:
#   cache_dir: Directorio de los archivos de caché (por defecto: "./cache").
# Retorna:
#   Tupla (symbols, tickers) o (None, None) si no hay caché disponible o es inválido.
Función load_market_data_from_cache(cache_dir):
  Si cache_dir no existe:
    Registrar advertencia.
    Retornar (None, None).
  Listar todos los archivos "market_data_*.json" en cache_dir.
  Si no hay archivos:
    Registrar advertencia.
    Retornar (None, None).
  Obtener el archivo más reciente (último en la lista ordenada).
  Intentar:
    Abrir y leer el archivo JSON.
    Extraer "symbols" y "tickers" del diccionario de datos.
    Si symbols o tickers están vacíos:
      Registrar advertencia de datos incompletos.
      Retornar (None, None).
    Registrar que los datos fueron cargados desde caché.
    Retornar (symbols, tickers).
  Excepto si hay error:
    Registrar error al cargar caché.
    Retornar (None, None).

# Función: list_available_cache_files
# Descripción: Lista los archivos de caché disponibles con su información.
# Parámetros:
#   cache_dir: Directorio de los archivos de caché (por defecto: "./cache").
# Retorna:
#   Lista de diccionarios con información de archivos de caché.
Función list_available_cache_files(cache_dir):
  Si cache_dir no existe:
    Retornar lista vacía.
  Inicializar lista cache_files vacía.
  Para cada filename en cache_dir:
    Si filename empieza con "market_data_" y termina con ".json":
      Construir filepath.
      Intentar:
        Abrir y leer el archivo JSON.
        Extraer timestamp, contar symbols y tickers.
        Formatear timestamp.
        Crear diccionario cache_info.
        Añadir cache_info a cache_files.
      Excepto si hay error:
        Registrar advertencia de error al procesar archivo.
  Ordenar cache_files por timestamp (más reciente primero).
  Retornar cache_files.

# Función: load_specific_cache_file
# Descripción: Carga los datos de mercado desde un archivo de caché específico.
# Parámetros:
#   filepath: Ruta del archivo de caché a cargar.
# Retorna:
#   Tupla (symbols, tickers) o (None, None) si hay error o datos incompletos.
Función load_specific_cache_file(filepath):
  Intentar:
    Abrir y leer el archivo JSON.
    Extraer "symbols" y "tickers" del diccionario de datos.
    Si symbols o tickers están vacíos:
      Registrar advertencia de datos incompletos.
      Retornar (None, None).
    Registrar que los datos fueron cargados desde caché específico.
    Retornar (symbols, tickers).
  Excepto si hay error:
    Registrar error al cargar caché específico.
    Retornar (None, None).

# Función: verificar_modulo_deteccion
# Descripción: Verifica que el módulo de detección de oportunidades esté correctamente configurado.
# Parámetros:
#   binance_client: Instancia del cliente de Binance.
# Retorna:
#   Diccionario con resultado de la verificación.
Función verificar_modulo_deteccion(binance_client):
  Intentar:
    Obtener mercados de Binance.
    Si no se obtienen mercados o la lista está vacía:
      Retornar fallo: "No se pudieron obtener los mercados de Binance".
    Si el número de mercados es menor a 100:
      Retornar fallo: "No hay suficientes mercados en Binance".
    Obtener tickers de Binance.
    Si no se obtienen tickers o la lista está vacía:
      Retornar fallo: "No se pudieron obtener los tickers de Binance".
    Verificar importación de la función calcular_rentabilidad_triangular.
    Retornar éxito: "Módulo de detección correctamente configurado".
  Excepto si hay error:
    Retornar fallo con mensaje de error.

# Función: fetch_market_data
# Descripción: Obtiene los símbolos y tickers, priorizando Mobula y usando Binance como fallback.
# Implementa limitación de symbols/tickers/parámetros por llamada API y soporte de caché.
# Parámetros:
#   binance_client: Instancia del cliente de Binance.
#   mobula_client: Instancia del cliente de Mobula.
#   token_search_limit: Límite de tokens a buscar en Mobula (por defecto: 400).
#   use_cache: Si True, intenta cargar datos desde caché primero (por defecto: False).
#   cache_dir: Directorio para los archivos de caché (por defecto: "./cache").
# Retorna:
#   Tupla (list of symbols, dict of tickers) o (None, None) si falla la obtención.
Función fetch_market_data(binance_client, mobula_client, token_search_limit=400, use_cache=False, cache_dir="./cache"):
  Si use_cache es True:
    Intentar cargar datos desde caché.
    Si se cargan datos válidos:
      Retornar (symbols, tickers).
    Registrar que no se encontró caché válido.
  Registrar inicio de obtención de datos.
  Inicializar symbols y tickers vacíos.
  mobula_failed = False.

  # Intentar obtener símbolos de Mobula
  Intentar:
    Obtener tokens top de Mobula con límite.
    Si se obtienen tokens:
      Extraer símbolos de los tokens (limitado por token_search_limit).
      Registrar número de símbolos obtenidos de Mobula.
    Si no se obtienen tokens:
      Registrar advertencia.
      mobula_failed = True.
  Excepto si hay error:
    Registrar error.
    mobula_failed = True.

  # Obtener tickers de Binance
  Intentar:
    Obtener todos los precios de Binance.
    Si se obtienen tickers:
      Filtrar tickers para mantener solo aquellos con precios válidos (> 0).
      Registrar número de tickers válidos obtenidos de Binance.
      Si Mobula falló o no hay símbolos:
        Obtener símbolos de trading de Binance.
        Si se obtienen símbolos de Binance:
          Filtrar símbolos de Binance para mantener solo aquellos que tienen tickers válidos.
          Actualizar lista de symbols.
          Registrar número de símbolos válidos usados de Binance.
        Si no se obtienen símbolos de Binance:
          Registrar error.
          Retornar (None, None).
    Si no se obtienen tickers de Binance:
      Registrar error.
      Retornar (None, None).
  Excepto si hay error:
    Registrar error.
    Retornar (None, None).

  Si symbols o tickers están vacíos:
    Registrar error.
    Retornar (None, None).

  Registrar fin de obtención de datos.
  Registrar ejemplos de symbols y tickers para debug.

  Si symbols y tickers son válidos:
    Intentar:
      Guardar datos en caché.
      Registrar que los datos fueron guardados en caché.
    Excepto si hay error:
      Registrar advertencia de fallo al guardar caché.

  Retornar (symbols, tickers).

# Función: find_opportunities
# Descripción: Encuentra oportunidades de arbitraje triangular dadas los símbolos, tickers y parámetros.
# Parámetros:
#   symbols: Lista de símbolos de trading disponibles.
#   tickers: Diccionario de tickers (símbolo: precio).
#   umbral_rentabilidad: Umbral de rentabilidad mínima (en porcentaje).
#   capital_inicial: Capital inicial sugerido para la operación.
#   fees_percentage: Lista de porcentajes de comisión por trade (por defecto: [0.1, 0.1, 0.1]).
# Retorna:
#   Lista de diccionarios con oportunidades encontradas.
Función find_opportunities(symbols, tickers, umbral_rentabilidad, capital_inicial, fees_percentage=None):
  Registrar inicio de búsqueda de oportunidades.
  Si fees_percentage es None, usar [0.1, 0.1, 0.1].
  Inicializar lista oportunidades_encontradas_list vacía.
  Convertir umbral_rentabilidad a decimal.

  Definir listas de COMMON_QUOTES y COMMON_BASES.
  Inicializar conjunto all_coins vacío.
  Inicializar contadores parsed_symbols_count y failed_parsing_count.

  # Diagnóstico: inspeccionar coincidencia entre símbolos y tickers (muestra)
  Inicializar contadores symbols_in_tickers y symbols_with_valid_price.
  Inicializar lista symbol_diagnostics.
  Recorrer una muestra de símbolos:
    Obtener precio del ticker.
    Verificar si el símbolo está en tickers y si el precio es válido.
    Almacenar diagnóstico en symbol_diagnostics.
    Incrementar contadores.
  Registrar diagnóstico de la muestra.

  # PROBLEMA/SOLUCIÓN: Coincidencia entre símbolos de Mobula y tickers de Binance
  Inicializar diccionario active_symbols vacío.
  Inicializar contador symbols_matched.
  # Probar coincidencia exacta primero
  Para cada symbol en symbols:
    Si symbol está en tickers y precio es válido:
      Añadir a active_symbols.
      Incrementar symbols_matched.

  # Si pocas coincidencias exactas, probar enfoque flexible
  Si symbols_matched es menor a 10:
    Registrar intento de coincidencia flexible.
    Crear mapas symbol_map y ticker_map (en mayúsculas).
    Para cada ticker_key en ticker_map:
      Para cada symbol_key en symbol_map:
        Si symbol_key está contenido en ticker_key o viceversa (y longitud > 2):
          Obtener ticker original y precio.
          Si precio es válido y ticker original no está en active_symbols:
            Añadir a active_symbols.
            Incrementar symbols_matched.
            Registrar coincidencia flexible (limitado).

  Registrar número de símbolos activos con ticker válido.

  # PROBLEMA/SOLUCIÓN: Con pocos símbolos activos, extraer monedas directamente de tickers
  Si len(active_symbols) es menor a 10:
    Registrar extracción de monedas directamente de tickers.
    Usar una muestra de tickers si hay demasiados.
    Definir extractores de monedas (patrones como USDT, BTC, ETH, BNB).
    Inicializar conjunto coins_extracted vacío.
    Para cada ticker en la muestra de tickers:
      Para cada extractor:
        Aplicar extractor al ticker.
        Si se obtiene resultado (moneda, cotización):
          Añadir moneda y cotización a coins_extracted.
    Añadir coins_extracted a all_coins.
    Registrar número de monedas extraídas.
  # Si hay suficientes símbolos activos, procesarlos para extraer monedas
  Si len(active_symbols) es mayor o igual a 10:
    Para cada symbol en active_symbols:
      Intentar:
        Inicializar base y quote a None.
        # Buscar por cotizaciones comunes
        Para cada common_quote:
          Si symbol termina con common_quote y base no está vacío:
            Extraer base y quote. Romper bucle.
        # Si no se encuentra por cotización, intentar por base común
        Si base o quote es None:
          Para cada common_base:
            Si symbol empieza con common_base y longitud es mayor:
              Extraer base y quote. Romper bucle.
        # Si aún no se encuentra, intentar dividir por la mitad (para símbolos de longitud razonable)
        Si base o quote es None y longitud de symbol está entre 5 y 12:
          Intentar dividir en diferentes puntos:
            Extraer potential_base y potential_quote.
            Si potential_base está en COMMON_BASES o potential_quote está en COMMON_QUOTES:
              Asignar base y quote. Romper bucle.
        # Si se identificó base y quote:
        Si base y quote son válidos:
          Añadir base y quote a all_coins.
          Incrementar parsed_symbols_count.
        Si no se identificó base y quote:
          Incrementar failed_parsing_count.
          Registrar fallo de parseo (limitado).
      Excepto si hay error:
        Incrementar failed_parsing_count.
        Registrar advertencia de error al parsear símbolo (limitado).

  Convertir all_coins a lista.
  Registrar número de monedas únicas identificadas.

  # Mejoras de rendimiento: limitar número de monedas para combinaciones
  Definir MAX_COINS_FOR_COMBINATIONS.
  Si len(all_coins) es mayor a MAX_COINS_FOR_COMBINATIONS:
    Priorizar monedas conocidas.
    Completar con otras monedas hasta el límite.
    Actualizar all_coins.
    Registrar que se limitó el número de monedas.

  # PROBLEMA/SOLUCIÓN: Usar correctamente los tickers
  Crear diccionario available_pairs.
  Si len(active_symbols) es mayor o igual a 10:
    Usar active_symbols para available_pairs.
    Registrar uso de símbolos activos.
  Si no:
    Usar todos los tickers válidos para available_pairs.
    Registrar uso de todos los tickers válidos.

  Registrar número de pares disponibles.

  Inicializar contadores total_combinations, valid_triangles, opportunities_above_threshold.
  Definir PROGRESS_LOG_INTERVAL.

  # Debugging: verificar si se pueden formar pares con una muestra de monedas
  Si total_combinations es 0 y len(all_coins) >= 3:
    Tomar una muestra de monedas.
    Para cada par de monedas en la muestra:
      Verificar si existe el par en available_pairs en ambas direcciones.
      Si se encuentra, registrar el par y su precio.
      Incrementar sample_pairs_found.
    Registrar número de pares encontrados en la muestra.

  # Procesar todas las combinaciones de 3 monedas
  Si len(all_coins) es menor a 3:
    Registrar advertencia.
  Si len(all_coins) es mayor o igual a 3:
    Para cada combinación de 3 monedas (coin_a, coin_b, coin_c) de all_coins:
      Incrementar total_combinations.
      Si total_combinations es múltiplo de PROGRESS_LOG_INTERVAL:
        Registrar progreso.

      # Encontrar los 3 pares necesarios (AB, BC, CA) en cualquier dirección
      Buscar pair_ab_symbol en available_pairs (A/B o B/A).
      Si no se encuentra pair_ab_symbol, continuar al siguiente ciclo.
      Buscar pair_bc_symbol en available_pairs (B/C o C/B).
      Si no se encuentra pair_bc_symbol, continuar al siguiente ciclo.
      Buscar pair_ca_symbol en available_pairs (C/A o A/C).

      # Si se encuentran los tres pares:
      Si pair_ab_symbol, pair_bc_symbol y pair_ca_symbol existen:
        Incrementar valid_triangles.
        Si es el primer triángulo válido, registrar detalles para debugging.

        Obtener precios price_ab, price_bc, price_ca de available_pairs.

        Si precios son válidos (> 0):
          # Ciclo 1: A -> B -> C -> A
          Intentar:
            Calcular factores factor_ab, factor_bc, factor_ca (considerando dirección y división por cero).
            Calcular rentabilidad bruta 1.
            Si rentabilidad bruta 1 es <= 0 o > 1000, continuar.
            Si rentabilidad bruta 1 > umbral_rentabilidad, incrementar opportunities_above_threshold.
            Registrar oportunidad encontrada (Ciclo 1).
            Calcular rentabilidad neta 1 usando calcular_rentabilidad_triangular.
            Determinar pasos y montos estimados para el Ciclo 1.
            Crear diccionario opportunity_data para el Ciclo 1.
            Añadir opportunity_data a oportunidades_encontradas_list.
          Excepto si hay error en cálculos del Ciclo 1:
            Registrar error de debug y continuar.

          # Ciclo 2: A -> C -> B -> A
          Intentar:
            Calcular factores factor_ac, factor_cb, factor_ba (considerando dirección y división por cero).
            Calcular rentabilidad bruta 2.
            Si rentabilidad bruta 2 es <= 0 o > 1000, continuar.
            Si rentabilidad bruta 2 > umbral_rentabilidad, incrementar opportunities_above_threshold.
            Registrar oportunidad encontrada (Ciclo 2).
            Calcular rentabilidad neta 2 usando calcular_rentabilidad_triangular.
            Determinar pasos y montos estimados para el Ciclo 2.
            Crear diccionario opportunity_data para el Ciclo 2.
            Añadir opportunity_data a oportunidades_encontradas_list.
          Excepto si hay error en cálculos del Ciclo 2:
            Registrar error de debug y continuar.

  # Filtrar oportunidades con rentabilidad neta negativa
  Crear lista filtered_opportunities con oportunidades donde profit_percentage_net > 0.
  Registrar cuántas oportunidades fueron filtradas.

  Retornar filtered_opportunities.

# Función: ejecutar_deteccion
# Descripción: Orquesta el proceso completo de detección y envío de oportunidades.
# Parámetros:
#   binance_client: Cliente de Binance.
#   mobula_client: Cliente de Mobula.
#   webhook_url: URL del webhook para enviar oportunidades (opcional).
#   use_cache: Si True, intenta usar datos del caché (por defecto: False).
#   cache_filepath: Si se especifica, usa un archivo de caché específico (opcional).
#   cache_dir: Directorio para archivos de caché (por defecto: "./cache").
# Retorna:
#   Lista de diccionarios con oportunidades encontradas.
Función ejecutar_deteccion(binance_client, mobula_client, webhook_url=None, use_cache=False, cache_filepath=None, cache_dir="./cache"):
  Registrar inicio de ejecución.
  Registrar parámetros de configuración.

  Intentar:
    # Verificar clientes
    Si binance_client es inválido:
      Registrar error.
      Retornar lista vacía.
    Si mobula_client es inválido:
      Registrar advertencia.

    # Obtener y validar parámetros de configuración (umbral, capital)
    Intentar:
      Obtener umbral_rentabilidad y capital_inicial de settings.
      Validar umbral y capital (mayor a 0). Usar valores predeterminados si son inválidos.
      Registrar valores de configuración.
      Si webhook_url está configurado, registrar URL (parcial).
      Si no, registrar que no se enviarán oportunidades.
    Excepto si hay AttributeError:
      Registrar error al acceder a configuración. Usar valores predeterminados.

    # Obtener datos de mercado
    Registrar inicio de obtención de datos de mercado.
    Si cache_filepath está especificado:
      Cargar datos desde archivo de caché específico.
    Si no:
      Obtener datos usando fetch_market_data (con opción use_cache).

    Si no se obtienen symbols o tickers:
      Registrar error.
      Retornar lista vacía.
    Registrar éxito en obtención de datos.

    # Buscar oportunidades
    Registrar inicio de búsqueda de oportunidades.
    Medir tiempo de búsqueda.
    Llamar a find_opportunities con los datos obtenidos y parámetros.

    # Procesar resultados
    Si se encuentran oportunidades:
      Registrar éxito y número de oportunidades encontradas.
      Ordenar oportunidades por rentabilidad neta y mostrar detalles de las mejores (limitado).
      Si webhook_url está configurado:
        Registrar inicio de envío a webhook.
        Inicializar contador successful_sent.
        Para cada oportunidad:
          Intentar:
            Formatear datos para Supabase (si aplica, aunque el código actual envía el dict completo).
            Enviar oportunidad a webhook usando requests.post.
            Verificar respuesta HTTP.
            Incrementar successful_sent.
            Registrar respuesta de webhook (limitado).
          Excepto si hay error de request:
            Registrar error al enviar oportunidad.
        Registrar resumen de envío a webhook.
      Si no hay webhook_url:
        Registrar que no se enviaron oportunidades.
    Si no se encuentran oportunidades:
      Registrar que no se encontraron oportunidades.
      Sugerir acciones (reducir umbral, ampliar rango).

  Excepto si hay error general:
    Registrar error general.
    Retornar lista vacía.

  Finalmente:
    Calcular tiempo total de ejecución.
    Registrar fin de detección.
    Retornar oportunidades encontradas.

# Función: run_detection_and_send_to_webhook
# Descripción: Ejecuta el proceso de detección con parámetros y envía resultados a webhook.
# Parámetros:
#   binance_client: Instancia del cliente de Binance.
#   mobula_client: Instancia del cliente de Mobula.
#   umbral_rentabilidad: Umbral mínimo de rentabilidad (en porcentaje).
#   capital_inicial: Capital inicial sugerido para la operación.
#   webhook_url: URL del webhook al que enviar las oportunidades (opcional).
# Retorna:
#   Lista de diccionarios con oportunidades encontradas.
Función run_detection_and_send_to_webhook(binance_client, mobula_client, umbral_rentabilidad, capital_inicial, webhook_url=None):
  Registrar inicio de ejecución con parámetros.
  Medir tiempo de inicio.

  Intentar:
    # Validar parámetros de entrada (umbral, capital)
    Si umbral_rentabilidad es negativo, usar valor absoluto.
    Si capital_inicial es <= 0, usar valor predeterminado 100.

    # Obtener datos de mercado
    Registrar inicio de obtención de datos.
    Llamar a fetch_market_data.
    Si no se obtienen symbols o tickers:
      Registrar error.
      Retornar lista vacía.
    Registrar éxito en obtención de datos.

    # Buscar oportunidades
    Registrar inicio de búsqueda.
    Medir tiempo de búsqueda.
    Llamar a find_opportunities con los datos obtenidos y parámetros.

    # Procesar resultados
    Si se encuentran oportunidades:
      Registrar número de oportunidades encontradas.
      Si webhook_url está configurado:
        Registrar inicio de envío a webhook.
        Inicializar contadores sent_count y failed_count.
        Para cada oportunidad:
          Intentar:
            Enviar oportunidad a webhook usando requests.post.
            Verificar respuesta HTTP.
            Incrementar sent_count.
            Registrar envío exitoso (limitado).
          Excepto si hay error de request:
            Incrementar failed_count.
            Registrar error al enviar oportunidad.
        Registrar resumen de envío.
      Si no hay webhook_url:
        Registrar que no se envió a webhook.
    Si no se encuentran oportunidades:
      Registrar que no se encontraron oportunidades.

  Excepto si hay error general:
    Registrar error general.
    Retornar lista vacía.

  Finalmente:
    Calcular tiempo total.
    Registrar fin del proceso.
    Retornar oportunidades encontradas.

# Bloque principal de ejecución (__main__)
Si el script se ejecuta directamente:
  Registrar inicio del script.
  Instanciar BinanceClient y MobulaClient.
  Si settings.n8n_webhook_oportunidad está configurado:
    Llamar a run_detection_and_send_to_webhook con clientes, umbral, capital y webhook_url.
  Si no:
    Llamar a ejecutar_deteccion con clientes.
  Registrar fin del script.

# Función: send_opportunities_to_webhook
# Descripción: Envía una lista de oportunidades a una URL de webhook especificada.
# Parámetros:
#   opportunities: Lista de diccionarios con oportunidades a enviar.
#   webhook_url: La URL del webhook.
# Retorna:
#   True si el envío fue exitoso para todas las oportunidades, False en caso contrario.
Función send_opportunities_to_webhook(opportunities, webhook_url):
  Registrar intento de envío a webhook.
  Inicializar success a True.
  Si webhook_url no está proporcionado:
    Registrar advertencia.
    Retornar False.

  Para cada opportunity_data en opportunities:
    Intentar:
      Enviar oportunidad a webhook usando requests.post.
      Lanzar excepción si la respuesta es mala (4xx o 5xx).
      Registrar envío exitoso con código de estado.
    Excepto si hay error de request:
      Registrar fallo al enviar oportunidad.
      Establecer success a False (pero continuar intentando enviar las demás).

  Retornar success.
