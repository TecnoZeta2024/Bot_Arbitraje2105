"""
Mobula API Integration
Enhanced market data and analytics from Mobula API
"""

import os
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal


class MobulaAPIClient:
    """
    Mobula API client for enhanced market data
    
    Features:
    - Real-time price data
    - Market analytics
    - Token information
    - Historical data
    """
    
    def __init__(self):
        self.api_key = os.getenv('MOBULA_API_KEY')
        self.base_url = "https://api.mobula.io/api/1"
        self.logger = logging.getLogger("api.mobula")
        
        if not self.api_key:
            self.logger.warning("Mobula API key not configured")
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info("Mobula API client initialized")
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """Make authenticated request to Mobula API"""
        
        if not self.enabled:
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/{endpoint}",
                    headers=headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Mobula API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Mobula API request failed: {e}")
            return None
    
    async def get_market_data(self, assets: List[str]) -> Optional[Dict]:
        """Get current market data for assets"""
        
        if not assets:
            return None
        
        params = {
            'assets': ','.join(assets),
            'blockchain': 'Ethereum'  # Default to Ethereum
        }
        
        response = await self._make_request('market/multi-data', params)
        
        if response and response.get('data'):
            processed_data = {}
            
            for asset_data in response['data']:
                symbol = asset_data.get('symbol', '').upper()
                if symbol:
                    processed_data[symbol] = {
                        'price': Decimal(str(asset_data.get('price', 0))),
                        'price_change_24h': asset_data.get('price_change_24h', 0),
                        'price_change_percentage_24h': asset_data.get('price_change_percentage_24h', 0),
                        'market_cap': asset_data.get('market_cap', 0),
                        'volume_24h': asset_data.get('volume_24h', 0),
                        'circulating_supply': asset_data.get('circulating_supply', 0),
                        'total_supply': asset_data.get('total_supply', 0),
                        'ath': asset_data.get('ath', 0),
                        'atl': asset_data.get('atl', 0),
                        'rank': asset_data.get('rank', 0),
                        'last_updated': datetime.now()
                    }
            
            return processed_data
        
        return None
    
    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """Get detailed token information"""
        
        params = {'asset': token_address}
        response = await self._make_request('metadata', params)
        
        if response and response.get('data'):
            data = response['data']
            return {
                'name': data.get('name'),
                'symbol': data.get('symbol'),
                'description': data.get('description'),
                'website': data.get('website'),
                'twitter': data.get('twitter'),
                'telegram': data.get('telegram'),
                'contracts': data.get('contracts', []),
                'logo': data.get('logo'),
                'total_supply': data.get('total_supply'),
                'max_supply': data.get('max_supply'),
                'tags': data.get('tags', [])
            }
        
        return None
    
    async def get_historical_data(self, asset: str, days: int = 30) -> Optional[List[Dict]]:
        """Get historical price data"""
        
        params = {
            'asset': asset,
            'from': int((datetime.now() - timedelta(days=days)).timestamp()),
            'to': int(datetime.now().timestamp())
        }
        
        response = await self._make_request('market/history', params)
        
        if response and response.get('data'):
            historical_data = []
            
            for data_point in response['data']['price_history']:
                historical_data.append({
                    'timestamp': datetime.fromtimestamp(data_point[0]),
                    'price': Decimal(str(data_point[1])),
                    'market_cap': data_point[2] if len(data_point) > 2 else None
                })
            
            return historical_data
        
        return None
    
    async def get_market_metrics(self, asset: str) -> Optional[Dict]:
        """Get advanced market metrics"""
        
        params = {'asset': asset}
        response = await self._make_request('market/metrics', params)
        
        if response and response.get('data'):
            data = response['data']
            return {
                'volatility_24h': data.get('volatility_24h', 0),
                'volatility_7d': data.get('volatility_7d', 0),
                'volume_to_market_cap': data.get('volume_to_market_cap', 0),
                'liquidity_score': data.get('liquidity_score', 0),
                'holder_count': data.get('holder_count', 0),
                'social_score': data.get('social_score', 0),
                'development_score': data.get('development_score', 0),
                'community_score': data.get('community_score', 0)
            }
        
        return None
    
    async def get_top_gainers_losers(self, limit: int = 10) -> Optional[Dict]:
        """Get top gainers and losers"""
        
        params = {
            'limit': limit,
            'order': 'price_change_percentage_24h',
            'direction': 'desc'
        }
        
        gainers_response = await self._make_request('market/data', params)
        
        params['direction'] = 'asc'
        losers_response = await self._make_request('market/data', params)
        
        result = {}
        
        if gainers_response and gainers_response.get('data'):
            result['gainers'] = [
                {
                    'symbol': item.get('symbol'),
                    'price': item.get('price'),
                    'change_24h': item.get('price_change_percentage_24h')
                }
                for item in gainers_response['data']
            ]
        
        if losers_response and losers_response.get('data'):
            result['losers'] = [
                {
                    'symbol': item.get('symbol'),
                    'price': item.get('price'),
                    'change_24h': item.get('price_change_percentage_24h')
                }
                for item in losers_response['data']
            ]
        
        return result if result else None
    
    async def search_tokens(self, query: str, limit: int = 10) -> Optional[List[Dict]]:
        """Search for tokens by name or symbol"""
        
        params = {
            'q': query,
            'limit': limit
        }
        
        response = await self._make_request('search', params)
        
        if response and response.get('data'):
            return [
                {
                    'name': item.get('name'),
                    'symbol': item.get('symbol'),
                    'address': item.get('contracts', [{}])[0].get('address') if item.get('contracts') else None,
                    'blockchain': item.get('contracts', [{}])[0].get('blockchain') if item.get('contracts') else None,
                    'logo': item.get('logo'),
                    'market_cap': item.get('market_cap'),
                    'price': item.get('price')
                }
                for item in response['data']
            ]
        
        return None
    
    async def get_portfolio_analytics(self, holdings: Dict[str, float]) -> Optional[Dict]:
        """Get portfolio analytics based on holdings"""
        
        if not holdings:
            return None
        
        # Get current prices for all holdings
        symbols = list(holdings.keys())
        market_data = await self.get_market_data(symbols)
        
        if not market_data:
            return None
        
        total_value = Decimal('0')
        portfolio_analytics = {
            'holdings': {},
            'total_value': 0,
            'total_change_24h': 0,
            'allocation': {},
            'risk_metrics': {}
        }
        
        for symbol, quantity in holdings.items():
            if symbol in market_data:
                asset_data = market_data[symbol]
                value = asset_data['price'] * Decimal(str(quantity))
                total_value += value
                
                portfolio_analytics['holdings'][symbol] = {
                    'quantity': quantity,
                    'price': float(asset_data['price']),
                    'value': float(value),
                    'change_24h': asset_data['price_change_percentage_24h']
                }
        
        # Calculate allocations and weighted metrics
        if total_value > 0:
            portfolio_analytics['total_value'] = float(total_value)
            
            weighted_change = Decimal('0')
            for symbol, holding in portfolio_analytics['holdings'].items():
                weight = Decimal(str(holding['value'])) / total_value
                portfolio_analytics['allocation'][symbol] = float(weight)
                weighted_change += weight * Decimal(str(holding['change_24h']))
            
            portfolio_analytics['total_change_24h'] = float(weighted_change)
        
        return portfolio_analytics
    
    async def get_trending_tokens(self, timeframe: str = '24h', limit: int = 20) -> Optional[List[Dict]]:
        """Get trending tokens"""
        
        params = {
            'timeframe': timeframe,
            'limit': limit
        }
        
        response = await self._make_request('market/trending', params)
        
        if response and response.get('data'):
            return [
                {
                    'symbol': item.get('symbol'),
                    'name': item.get('name'),
                    'price': item.get('price'),
                    'change_24h': item.get('price_change_percentage_24h'),
                    'volume_24h': item.get('volume_24h'),
                    'market_cap': item.get('market_cap'),
                    'trending_score': item.get('trending_score', 0)
                }
                for item in response['data']
            ]
        
        return None


# Global instance
mobula_client = MobulaAPIClient()
