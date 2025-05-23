"""
Supabase Database Integration
Handles data persistence for trading operations, metrics, and configuration
"""

import asyncio
import logging
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import asyncpg

from ...domain.risk_management.advanced_risk_manager import PositionInfo, RiskEvent
from ...domain.trading_signals.trading_signal import TradingSignal


class SupabaseClient:
    """
    Supabase database client for trading application
    
    Handles:
    - Trading operations logging
    - Performance metrics storage
    - System configuration
    - Risk events tracking
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        self.connection_pool = None
        self.logger = logging.getLogger("database.supabase")
        
        if not all([self.supabase_url, self.anon_key, self.service_key]):
            raise ValueError("Missing Supabase configuration")
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            # Extract database connection info from Supabase URL
            db_config = self._parse_supabase_config()
            
            self.connection_pool = await asyncpg.create_pool(
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            self.logger.info("Supabase connection pool initialized")
            
            # Verify tables exist
            await self._verify_tables()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase connection: {e}")
            raise
    
    def _parse_supabase_config(self) -> Dict[str, Any]:
        """Parse Supabase URL to extract connection parameters"""
        # For production, you would parse the actual connection string
        # For now, using default Supabase PostgreSQL configuration
        return {
            'host': 'db.almhlhmijfkcvmdbidvw.supabase.co',
            'port': 5432,
            'database': 'postgres',
            'user': 'postgres',
            'password': os.getenv('SUPABASE_DB_PASSWORD', 'your_db_password')  # Set this in .env
        }
    
    async def _verify_tables(self):
        """Verify that required tables exist"""
        required_tables = [
            'arbitraje_operaciones',
            'configuracion_sistema', 
            'metricas_rendimiento'
        ]
        
        async with self.connection_pool.acquire() as connection:
            for table in required_tables:
                exists = await connection.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                
                if exists:
                    self.logger.info(f"Table '{table}' verified")
                else:
                    self.logger.warning(f"Table '{table}' does not exist - creating...")
                    await self._create_table(connection, table)
    
    async def _create_table(self, connection, table_name: str):
        """Create required tables if they don't exist"""
        
        table_schemas = {
            'arbitraje_operaciones': """
                CREATE TABLE IF NOT EXISTS arbitraje_operaciones (
                    id SERIAL PRIMARY KEY,
                    signal_id VARCHAR(255) UNIQUE NOT NULL,
                    strategy_name VARCHAR(100) NOT NULL,
                    symbol VARCHAR(50) NOT NULL,
                    action VARCHAR(20) NOT NULL,
                    entry_price DECIMAL(20, 8),
                    exit_price DECIMAL(20, 8),
                    quantity DECIMAL(20, 8),
                    pnl DECIMAL(20, 8),
                    commission DECIMAL(20, 8),
                    confidence DECIMAL(5, 4),
                    risk_level VARCHAR(20),
                    entry_time TIMESTAMP WITH TIME ZONE,
                    exit_time TIMESTAMP WITH TIME ZONE,
                    hold_duration_seconds INTEGER,
                    ai_analysis JSONB,
                    market_conditions JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_arbitraje_operaciones_strategy ON arbitraje_operaciones(strategy_name);
                CREATE INDEX IF NOT EXISTS idx_arbitraje_operaciones_symbol ON arbitraje_operaciones(symbol);
                CREATE INDEX IF NOT EXISTS idx_arbitraje_operaciones_entry_time ON arbitraje_operaciones(entry_time);
            """,
            
            'configuracion_sistema': """
                CREATE TABLE IF NOT EXISTS configuracion_sistema (
                    id SERIAL PRIMARY KEY,
                    config_key VARCHAR(255) UNIQUE NOT NULL,
                    config_value JSONB NOT NULL,
                    description TEXT,
                    category VARCHAR(100),
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_configuracion_sistema_key ON configuracion_sistema(config_key);
                CREATE INDEX IF NOT EXISTS idx_configuracion_sistema_category ON configuracion_sistema(category);
            """,
            
            'metricas_rendimiento': """
                CREATE TABLE IF NOT EXISTS metricas_rendimiento (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    strategy_name VARCHAR(100),
                    symbol VARCHAR(50),
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value DECIMAL(20, 8),
                    metric_data JSONB,
                    period_start TIMESTAMP WITH TIME ZONE,
                    period_end TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_metricas_rendimiento_timestamp ON metricas_rendimiento(timestamp);
                CREATE INDEX IF NOT EXISTS idx_metricas_rendimiento_strategy ON metricas_rendimiento(strategy_name);
                CREATE INDEX IF NOT EXISTS idx_metricas_rendimiento_metric ON metricas_rendimiento(metric_name);
            """
        }
        
        if table_name in table_schemas:
            await connection.execute(table_schemas[table_name])
            self.logger.info(f"Table '{table_name}' created successfully")
    
    async def log_trading_operation(self, signal: TradingSignal, position: Optional[PositionInfo] = None):
        """Log a trading operation to the database"""
        
        try:
            async with self.connection_pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO arbitraje_operaciones (
                        signal_id, strategy_name, symbol, action, entry_price, 
                        quantity, confidence, risk_level, entry_time, 
                        ai_analysis, market_conditions
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (signal_id) DO NOTHING
                """, 
                    signal.signal_id,
                    signal.strategy_name.value,
                    signal.symbol,
                    signal.action.value,
                    float(signal.entry_price) if signal.entry_price else None,
                    float(position.quantity) if position else None,
                    float(signal.confidence),
                    signal.risk_level.value,
                    signal.timestamp,
                    signal.ai_analysis,
                    signal.market_conditions
                )
                
                self.logger.info(f"Trading operation logged: {signal.signal_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to log trading operation: {e}")
    
    async def update_operation_exit(self, signal_id: str, exit_price: Decimal, pnl: Decimal, commission: Decimal):
        """Update operation with exit details"""
        
        try:
            async with self.connection_pool.acquire() as connection:
                result = await connection.execute("""
                    UPDATE arbitraje_operaciones 
                    SET exit_price = $2, pnl = $3, commission = $4, 
                        exit_time = NOW(), 
                        hold_duration_seconds = EXTRACT(EPOCH FROM (NOW() - entry_time)),
                        updated_at = NOW()
                    WHERE signal_id = $1
                """, signal_id, float(exit_price), float(pnl), float(commission))
                
                self.logger.info(f"Operation exit updated: {signal_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to update operation exit: {e}")
    
    async def save_performance_metrics(self, metrics: Dict[str, Any], strategy_name: str = None):
        """Save performance metrics to database"""
        
        try:
            async with self.connection_pool.acquire() as connection:
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, (int, float, Decimal)):
                        await connection.execute("""
                            INSERT INTO metricas_rendimiento (
                                strategy_name, metric_name, metric_value, timestamp
                            ) VALUES ($1, $2, $3, NOW())
                        """, strategy_name, metric_name, float(metric_value))
                    
                    elif isinstance(metric_value, dict):
                        await connection.execute("""
                            INSERT INTO metricas_rendimiento (
                                strategy_name, metric_name, metric_data, timestamp
                            ) VALUES ($1, $2, $3, NOW())
                        """, strategy_name, metric_name, metric_value)
                
                self.logger.info(f"Performance metrics saved for {strategy_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to save performance metrics: {e}")
    
    async def get_configuration(self, config_key: str) -> Optional[Dict]:
        """Get system configuration by key"""
        
        try:
            async with self.connection_pool.acquire() as connection:
                result = await connection.fetchrow("""
                    SELECT config_value FROM configuracion_sistema 
                    WHERE config_key = $1 AND is_active = true
                """, config_key)
                
                return result['config_value'] if result else None
                
        except Exception as e:
            self.logger.error(f"Failed to get configuration {config_key}: {e}")
            return None
    
    async def save_configuration(self, config_key: str, config_value: Dict, description: str = None, category: str = None):
        """Save or update system configuration"""
        
        try:
            async with self.connection_pool.acquire() as connection:
                await connection.execute("""
                    INSERT INTO configuracion_sistema (config_key, config_value, description, category)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (config_key) 
                    DO UPDATE SET 
                        config_value = EXCLUDED.config_value,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        updated_at = NOW()
                """, config_key, config_value, description, category)
                
                self.logger.info(f"Configuration saved: {config_key}")
                
        except Exception as e:
            self.logger.error(f"Failed to save configuration {config_key}: {e}")
    
    async def get_trading_history(self, strategy_name: str = None, symbol: str = None, 
                                limit: int = 100, days: int = 30) -> List[Dict]:
        """Get trading history with optional filters"""
        
        try:
            async with self.connection_pool.acquire() as connection:
                where_conditions = ["entry_time >= NOW() - INTERVAL '%s days'" % days]
                params = []
                param_count = 0
                
                if strategy_name:
                    param_count += 1
                    where_conditions.append(f"strategy_name = ${param_count}")
                    params.append(strategy_name)
                
                if symbol:
                    param_count += 1
                    where_conditions.append(f"symbol = ${param_count}")
                    params.append(symbol)
                
                param_count += 1
                params.append(limit)
                
                query = f"""
                    SELECT * FROM arbitraje_operaciones 
                    WHERE {' AND '.join(where_conditions)}
                    ORDER BY entry_time DESC 
                    LIMIT ${param_count}
                """
                
                results = await connection.fetch(query, *params)
                return [dict(row) for row in results]
                
        except Exception as e:
            self.logger.error(f"Failed to get trading history: {e}")
            return []
    
    async def get_performance_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get performance summary for the last N days"""
        
        try:
            async with self.connection_pool.acquire() as connection:
                # Get basic stats
                stats = await connection.fetchrow("""
                    SELECT 
                        COUNT(*) as total_trades,
                        COUNT(*) FILTER (WHERE pnl > 0) as winning_trades,
                        COUNT(*) FILTER (WHERE pnl < 0) as losing_trades,
                        SUM(pnl) as total_pnl,
                        AVG(pnl) as avg_pnl,
                        MAX(pnl) as best_trade,
                        MIN(pnl) as worst_trade,
                        AVG(confidence) as avg_confidence,
                        AVG(hold_duration_seconds) as avg_hold_time_seconds
                    FROM arbitraje_operaciones 
                    WHERE entry_time >= NOW() - INTERVAL '%s days'
                    AND exit_time IS NOT NULL
                """ % days)
                
                # Get strategy breakdown
                strategy_stats = await connection.fetch("""
                    SELECT 
                        strategy_name,
                        COUNT(*) as trades,
                        SUM(pnl) as pnl,
                        AVG(confidence) as avg_confidence
                    FROM arbitraje_operaciones 
                    WHERE entry_time >= NOW() - INTERVAL '%s days'
                    AND exit_time IS NOT NULL
                    GROUP BY strategy_name
                """ % days)
                
                return {
                    'summary': dict(stats) if stats else {},
                    'by_strategy': [dict(row) for row in strategy_stats],
                    'period_days': days
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {e}")
            return {}
    
    async def close(self):
        """Close database connections"""
        if self.connection_pool:
            await self.connection_pool.close()
            self.logger.info("Supabase connection pool closed")


# Global instance - initialize only when needed to avoid import errors
supabase_client = None

def get_supabase_client():
    """Get or create Supabase client instance"""
    global supabase_client
    if supabase_client is None:
        try:
            supabase_client = SupabaseClient()
        except ValueError as e:
            # Return None if configuration is missing
            logging.getLogger("database.supabase").warning(f"Supabase client not initialized: {e}")
            return None
    return supabase_client
