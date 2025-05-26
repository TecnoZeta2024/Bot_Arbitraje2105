"""
Módulo para la detección de anomalías en datos de series temporales financieras.

Algoritmos seleccionados para la implementación inicial:
1.  Z-score:
    -   Justificación: Simplicidad, facilidad de implementación y buena para detectar anomalías en datos que se aproximan a una distribución normal.
        Útil para identificar picos o caídas repentinas en precios y volúmenes.
2.  Isolation Forest:
    -   Justificación: Algoritmo de aprendizaje automático no supervisado, robusto a valores atípicos y eficaz para conjuntos de datos de alta dimensión.
        No asume una distribución de datos específica y es bueno para detectar anomalías complejas.

Este módulo procesará datos normalizados y marcará las anomalías detectadas.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import Optional

from src.utils.logger import get_logger
from src.infrastructure.messaging.notification_service import NotificationService, MessageType, MessagePriority

class AnomalyDetector:
    def __init__(self, z_score_threshold: float = 3.0, contamination: float = 0.01):
        """
        Inicializa el detector de anomalías con los umbrales para Z-score y Isolation Forest.

        Args:
            z_score_threshold (float): Umbral para la detección de anomalías basada en Z-score.
                                       Un valor común es 2.0 o 3.0.
            contamination (float): La proporción esperada de anomalías en el conjunto de datos.
                                   Utilizado por Isolation Forest.
        """
        self.z_score_threshold = z_score_threshold
        self.isolation_forest_model = IsolationForest(contamination=contamination, random_state=42)
        self.logger = get_logger('anomaly_detector')
        self.notification_service = NotificationService() # Asume que el servicio se inicializa y configura globalmente
        # Umbral para enviar alertas (ej. número mínimo de anomalías para activar una alerta)
        self.alert_threshold = 1 # Por ahora, cualquier anomalía dispara una alerta

    def detect_anomalies_z_score(self, data: pd.Series) -> pd.Series:
        """
        Detecta anomalías en una serie de datos utilizando el método Z-score.

        Args:
            data (pd.Series): Serie de datos numéricos.

        Returns:
            pd.Series: Serie booleana donde True indica una anomalía.
        """
        if data.empty or data.std() == 0:
            return pd.Series([False] * len(data), index=data.index)

        mean = data.mean()
        std = data.std()
        z_scores = np.abs((data - mean) / std)
        return pd.Series(z_scores > self.z_score_threshold, index=data.index)

    def detect_anomalies_isolation_forest(self, data: pd.DataFrame) -> pd.Series:
        """
        Detecta anomalías en un DataFrame utilizando Isolation Forest.

        Args:
            data (pd.DataFrame): DataFrame de datos numéricos.

        Returns:
            pd.Series: Serie booleana donde True indica una anomalía.
        """
        if data.empty:
            return pd.Series([False] * len(data), index=data.index)

        self.isolation_forest_model.fit(data)
        # decision_function devuelve la puntuación de anomalía, lower is more anomalous
        # predict devuelve -1 para anomalías y 1 para valores normales
        predictions = self.isolation_forest_model.predict(data)
        return pd.Series(predictions == -1, index=data.index)

    async def detect_anomalies(self, data: pd.DataFrame, columns_for_z_score: Optional[list[str]] = None) -> pd.DataFrame:
        """
        Detecta anomalías utilizando una combinación de Z-score (para columnas específicas)
        y Isolation Forest (para el conjunto de datos completo), y registra/alerta sobre ellas.

        Args:
            data (pd.DataFrame): DataFrame de datos normalizados.
            columns_for_z_score (list): Lista de nombres de columnas para aplicar Z-score.
                                        Si es None, no se aplica Z-score.

        Returns:
            pd.DataFrame: DataFrame con columnas adicionales indicando anomalías.
                          'is_anomaly_z_score_{column_name}' para Z-score y 'is_anomaly_isolation_forest'.
        """
        anomalies_df = pd.DataFrame(index=data.index)

        # Detección de anomalías con Z-score para columnas específicas
        if columns_for_z_score:
            for col in columns_for_z_score:
                if col in data.columns:
                    anomalies_df[f'is_anomaly_z_score_{col}'] = self.detect_anomalies_z_score(data[col])
                else:
                    self.logger.warning(f"Columna '{col}' no encontrada para detección Z-score.")

        # Detección de anomalías con Isolation Forest para el DataFrame completo
        numeric_data = data.select_dtypes(include=np.number)
        if not numeric_data.empty:
            anomalies_df['is_anomaly_isolation_forest'] = self.detect_anomalies_isolation_forest(numeric_data)
        else:
            anomalies_df['is_anomaly_isolation_forest'] = False

        # Combinar resultados
        if not anomalies_df.empty:
            anomalies_df['is_overall_anomaly'] = anomalies_df.any(axis=1)
        else:
            anomalies_df['is_overall_anomaly'] = False

        # Logging y Alertas de anomalías
        anomalous_rows = data[anomalies_df['is_overall_anomaly']]
        if not anomalous_rows.empty:
            num_anomalies = len(anomalous_rows)
            log_message = f"Se detectaron {num_anomalies} anomalías. Detalles:\n{anomalous_rows.to_string()}"
            self.logger.warning(log_message)

            if num_anomalies >= self.alert_threshold:
                alert_title = f"🚨 Alerta de Anomalía: {num_anomalies} detectadas"
                alert_content = f"Se han detectado {num_anomalies} anomalías en los datos. " \
                                f"Primeras 5 anomalías:\n{anomalous_rows.head().to_string()}"
                
                # Asegurarse de que el servicio de notificación esté iniciado
                if not self.notification_service.router.is_running:
                    await self.notification_service.start()

                await self.notification_service.notify_critical_alert(
                    title=alert_title,
                    message=alert_content,
                    component="AnomalyDetector"
                )
                self.logger.info(f"Alerta de anomalía enviada: {alert_title}")

        return anomalies_df

if __name__ == "__main__":
    # Ejemplo de uso
    import asyncio
    np.random.seed(42)
    data = {
        'price': np.random.normal(100, 5, 100),
        'volume': np.random.normal(1000, 100, 100),
        'profit': np.random.normal(0.01, 0.001, 100)
    }
    df = pd.DataFrame(data)

    # Introducir algunas anomalías
    df.loc[10, 'price'] = 150
    df.loc[25, 'volume'] = 5000
    df.loc[50, 'profit'] = 0.1
    df.loc[51, 'price'] = 160 # Otra anomalía para probar el umbral

    async def main():
        detector = AnomalyDetector(z_score_threshold=3.0, contamination=0.02)
        anomalies = await detector.detect_anomalies(df, columns_for_z_score=['price', 'volume'])

        print("DataFrame original con anomalías inyectadas:")
        print(df.head())
        print("\nResultados de detección de anomalías:")
        print(anomalies.head())
        print("\nResumen de anomalías detectadas:")
        print(anomalies['is_overall_anomaly'].value_counts())

        # Mostrar las filas que son anomalías
        anomalous_rows = df[anomalies['is_overall_anomaly']]
        print("\nFilas detectadas como anomalías:")
        print(anomalous_rows)

        # Detener el servicio de notificación si se inició en el main
        if detector.notification_service.router.is_running:
            await detector.notification_service.stop()

    asyncio.run(main())
