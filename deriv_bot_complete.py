#!/usr/bin/env python3
"""
Deriv Bot v2.0 - Complete Standalone Application
Professional trading bot with embedded configuration, advanced prediction engine, 
machine learning, and comprehensive risk management
Author: umbrellabadbro-star
"""

import os
import json
import time
import logging
import threading
import queue
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    import websocket
    import requests
    from dotenv import load_dotenv
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system("pip install websocket-client requests python-dotenv numpy")
    import websocket
    import requests
    from dotenv import load_dotenv
    import numpy as np

# Load environment variables
load_dotenv()

# Create directories
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_trades.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATACLASSES
# ============================================================================

class TradeType(Enum):
    """Trade types supported"""
    DIGITS_MATCH = "DIGITMATCH"
    DIGITS_DIFFER = "DIGITDIFF"
    RISE = "CALL"
    FALL = "PUT"


class StrategyType(Enum):
    """Strategy types"""
    MATCH = "match"
    DIFFER = "differ"


@dataclass
class Trade:
    """Trade record"""
    trade_id: str
    symbol: str
    amount: float
    direction: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    profit_loss: float = 0
    status: str = "open"
    confidence: float = 0


# ============================================================================
# EMBEDDED CONFIGURATION
# ============================================================================

DEFAULT_CONFIG_XML = """<?xml version="1.0" encoding="UTF-8"?>
<deriv_bot>
    <connection_config>
        <endpoint>wss://ws.binaryws.com/websockets/v3</endpoint>
        <connection_timeout>30000</connection_timeout>
        <reconnect_attempts>5</reconnect_attempts>
        <reconnect_delay>2000</reconnect_delay>
        <heartbeat_interval>30000</heartbeat_interval>
        <max_idle_timeout>60000</max_idle_timeout>
    </connection_config>

    <account_config>
        <account_type>real</account_type>
        <currency>USD</currency>
        <server>default</server>
        <auto_balance_check>true</auto_balance_check>
        <balance_check_interval>60000</balance_check_interval>
    </account_config>

    <trade_config>
        <symbol>FRXUSDJPY</symbol>
        <trade_type>digits_match</trade_type>
        <stake>10</stake>
        <duration>1m</duration>
        <duration_value>60</duration_value>
        <max_concurrent_trades>1</max_concurrent_trades>
        <min_stake>1</min_stake>
        <max_stake>1000</max_stake>
        <daily_profit_target>100</daily_profit_target>
        <daily_loss_limit>500</daily_loss_limit>
        <consecutive_loss_limit>5</consecutive_loss_limit>
        <allow_same_symbol>true</allow_same_symbol>
    </trade_config>

    <prediction_engine>
        <strategy>advanced_adaptive</strategy>
        <prediction_mode>auto_switch</prediction_mode>
        <prediction_interval>3000</prediction_interval>
        <min_data_points>10</min_data_points>
        
        <indicators>
            <rsi>
                <enabled>true</enabled>
                <period>14</period>
                <overbought>70</overbought>
                <oversold>30</oversold>
                <weight>0.25</weight>
            </rsi>
            <moving_average>
                <enabled>true</enabled>
                <type>exponential</type>
                <fast_period>12</fast_period>
                <slow_period>26</slow_period>
                <weight>0.25</weight>
            </moving_average>
            <bollinger_bands>
                <enabled>true</enabled>
                <period>20</period>
                <std_dev>2</std_dev>
                <weight>0.20</weight>
            </bollinger_bands>
            <macd>
                <enabled>true</enabled>
                <fast_period>12</fast_period>
                <slow_period>26</slow_period>
                <signal_period>9</signal_period>
                <weight>0.20</weight>
            </macd>
            <stochastic>
                <enabled>true</enabled>
                <k_period>14</k_period>
                <d_period>3</d_period>
                <smooth>3</smooth>
                <weight>0.10</weight>
            </stochastic>
        </indicators>

        <adaptive_learning>
            <enabled>true</enabled>
            <learning_rate>0.02</learning_rate>
            <momentum>0.95</momentum>
            <memory_size>1000</memory_size>
            <pattern_detection>true</pattern_detection>
            <pattern_min_occurrences>3</pattern_min_occurrences>
            <win_rate_threshold>55</win_rate_threshold>
            <model_update_interval>5</model_update_interval>
        </adaptive_learning>

        <random_tick_generation>
            <enabled>false</enabled>
            <min_value>0</min_value>
            <max_value>9</max_value>
            <tick_interval>1000</tick_interval>
            <distribution>normal</distribution>
        </random_tick_generation>

        <digits_logic>
            <sample_size>30</sample_size>
            <match_prediction_weight>0.45</match_prediction_weight>
            <differ_prediction_weight>0.55</differ_prediction_weight>
            <confidence_threshold>65</confidence_threshold>
            <auto_switch_threshold>52</auto_switch_threshold>
            <use_entropy>true</use_entropy>
            <use_markov_chain>true</use_markov_chain>
        </digits_logic>

        <volatility_analysis>
            <enabled>true</enabled>
            <period>20</period>
            <high_threshold>0.75</high_threshold>
            <low_threshold>0.25</low_threshold>
            <adjust_stake_on_volatility>true</adjust_stake_on_volatility>
        </volatility_analysis>
    </prediction_engine>

    <risk_management>
        <enabled>true</enabled>
        <max_risk_per_trade>3</max_risk_per_trade>
        <max_drawdown_percentage>15</max_drawdown_percentage>
        
        <position_sizing>
            <method>kelly_criterion</method>
            <kelly_fraction>0.25</kelly_fraction>
            <min_bet_multiplier>0.5</min_bet_multiplier>
            <max_bet_multiplier>2.0</max_bet_multiplier>
        </position_sizing>

        <martingale>
            <enabled>false</enabled>
            <multiplier>2</multiplier>
            <max_steps>3</max_steps>
            <reset_on_win>true</reset_on_win>
        </martingale>

        <stop_loss>
            <enabled>true</enabled>
            <loss_percentage>10</loss_percentage>
            <trailing_stop>true</trailing_stop>
            <trailing_percentage>5</trailing_percentage>
        </stop_loss>

        <take_profit>
            <enabled>true</enabled>
            <profit_percentage>20</profit_percentage>
            <partial_exit>true</partial_exit>
            <partial_exit_percentage>50</partial_exit_percentage>
        </take_profit>

        <circuit_breaker>
            <enabled>true</enabled>
            <consecutive_losses_trigger>3</consecutive_losses_trigger>
            <cooldown_period>300000</cooldown_period>
        </circuit_breaker>
    </risk_management>

    <performance_tracking>
        <enabled>true</enabled>
        <log_file>logs/bot_trades.log</log_file>
        <session_file>logs/bot_session.json</session_file>
        <stats_file>logs/bot_stats.json</stats_file>
        <update_interval>10000</update_interval>
        
        <metrics>
            <track_win_rate>true</track_win_rate>
            <track_roi>true</track_roi>
            <track_accuracy>true</track_accuracy>
            <track_prediction_confidence>true</track_prediction_confidence>
            <track_drawdown>true</track_drawdown>
            <track_sharpe_ratio>true</track_sharpe_ratio>
            <track_volatility>true</track_volatility>
        </metrics>

        <alerts>
            <high_win_rate_threshold>75</high_win_rate_threshold>
            <low_win_rate_threshold>40</low_win_rate_threshold>
            <alert_on_anomaly>true</alert_on_anomaly>
        </alerts>
    </performance_tracking>

    <notifications>
        <enabled>true</enabled>
        <webhook_url></webhook_url>
        <discord_webhook></discord_webhook>
        <telegram_token></telegram_token>
        <telegram_chat_id></telegram_chat_id>
        
        <notify_on>
            <winning_trade>true</winning_trade>
            <losing_trade>false</losing_trade>
            <milestone>true</milestone>
            <daily_summary>true</daily_summary>
            <weekly_summary>true</weekly_summary>
            <error>true</error>
            <strategy_change>true</strategy_change>
            <circuit_breaker_triggered>true</circuit_breaker_triggered>
        </notify_on>

        <notification_frequency>
            <min_interval_between_trades>1000</min_interval_between_trades>
            <batch_notifications>true</batch_notifications>
        </notification_frequency>
    </notifications>

    <execution_schedule>
        <enabled>true</enabled>
        <start_time>00:00</start_time>
        <end_time>23:59</end_time>
        <timezone>UTC</timezone>
        <pause_during_news_events>false</pause_during_news_events>
        
        <trading_days>
            <monday>true</monday>
            <tuesday>true</tuesday>
            <wednesday>true</wednesday>
            <thursday>true</thursday>
            <friday>true</friday>
            <saturday>false</saturday>
            <sunday>false</sunday>
        </trading_days>

        <market_hours>
            <region>forex</region>
            <respect_market_hours>false</respect_market_hours>
            <pause_before_news>0</pause_before_news>
            <resume_after_news>0</resume_after_news>
        </market_hours>
    </execution_schedule>

    <data_management>
        <enabled>true</enabled>
        <cache_enabled>true</cache_enabled>
        <max_cache_size>10000</max_cache_size>
        <backup_interval>3600000</backup_interval>
        <data_retention_days>30</data_retention_days>
    </data_management>

    <debug>
        <enabled>false</enabled>
        <log_level>INFO</log_level>
        <verbose_predictions>false</verbose_predictions>
        <simulate_trades>false</simulate_trades>
        <log_api_responses>false</log_api_responses>
        <performance_profiling>false</performance_profiling>
    </debug>
</deriv_bot>
"""


# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================

class ConfigManager:
    """Manage bot configuration from embedded XML or external file"""
    
    def __init__(self, config_file: str = 'bot_config.xml'):
        self.config_file = config_file
        self.config_data = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or use embedded default"""
        if os.path.exists(self.config_file):
            try:
                tree = ET.parse(self.config_file)
                root = tree.getroot()
                logger.info(f"Loaded configuration from {self.config_file}")
            except ET.ParseError as e:
                logger.warning(f"Error parsing config file: {e}, using default")
                root = ET.fromstring(DEFAULT_CONFIG_XML)
        else:
            logger.info("Using embedded default configuration")
            root = ET.fromstring(DEFAULT_CONFIG_XML)
        
        self.config_data = self._parse_xml(root)
    
    def _parse_xml(self, root) -> Dict:
        """Parse XML element tree"""
        config = {}
        
        for child in root:
            section = child.tag
            config[section] = {}
            
            for element in child:
                key = element.tag
                value = element.text
                
                if value is None:
                    value = None
                elif isinstance(value, str):
                    if value.lower() in ['true', 'false']:
                        value = value.lower() == 'true'
                    elif value.isdigit():
                        value = int(value)
                    else:
                        try:
                            value = float(value)
                        except (ValueError, AttributeError):
                            pass
                
                config[section][key] = value
        
        return config
    
    def get(self, section: str, key: str, default=None):
        """Get configuration value safely"""
        try:
            return self.config_data.get(section, {}).get(key, default)
        except Exception as e:
            logger.warning(f"Error getting config {section}.{key}: {e}")
            return default
    
    def save_default_config(self):
        """Save default configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                f.write(DEFAULT_CONFIG_XML)
            logger.info(f"Saved default configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")


# ============================================================================
# PREDICTION ENGINE
# ============================================================================

class PredictionEngine:
    """Advanced prediction engine with adaptive learning"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.tick_history = deque(maxlen=int(config.get('prediction_engine', 'memory_size', 1000)))
        self.trade_history = deque(maxlen=500)
        self.pattern_memory = {}
        self.win_rate = 0.5
        self.current_strategy = StrategyType.MATCH
        self.prediction_accuracy = 0.5
        self.learning_rate = float(config.get('prediction_engine', 'learning_rate', 0.02))
        logger.info("Prediction engine initialized")
    
    def add_tick(self, tick_value: int):
        """Add tick to history"""
        try:
            self.tick_history.append({
                'value': int(tick_value),
                'timestamp': datetime.now()
            })
            self._update_patterns()
        except Exception as e:
            logger.warning(f"Error adding tick: {e}")
    
    def _update_patterns(self):
        """Update pattern memory"""
        if len(self.tick_history) < 5:
            return
        
        recent = [t['value'] for t in list(self.tick_history)[-5:]]
        pattern = tuple(recent)
        
        if pattern not in self.pattern_memory:
            self.pattern_memory[pattern] = {'count': 0, 'wins': 0, 'accuracy': 0.5}
        
        self.pattern_memory[pattern]['count'] += 1
    
    def calculate_rsi(self, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(self.tick_history) < period:
            return 50.0
        
        try:
            values = np.array([t['value'] for t in list(self.tick_history)[-period:]], dtype=float)
            deltas = np.diff(values)
            
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains) if len(gains) > 0 else 0
            avg_loss = np.mean(losses) if len(losses) > 0 else 0
            
            if avg_loss == 0:
                return 100.0 if avg_gain > 0 else 50.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi)
        except Exception as e:
            logger.warning(f"RSI calculation error: {e}")
            return 50.0
    
    def calculate_stochastic(self, k_period: int = 14) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator"""
        if len(self.tick_history) < k_period:
            return 50.0, 50.0
        
        try:
            values = np.array([t['value'] for t in list(self.tick_history)[-k_period:]], dtype=float)
            lowest = np.min(values)
            highest = np.max(values)
            
            if highest == lowest:
                return 50.0, 50.0
            
            k = 100 * (values[-1] - lowest) / (highest - lowest)
            d = np.mean([k])
            
            return float(k), float(d)
        except Exception as e:
            logger.warning(f"Stochastic calculation error: {e}")
            return 50.0, 50.0
    
    def calculate_ema(self, period: int = 20) -> float:
        """Calculate Exponential Moving Average"""
        if len(self.tick_history) < period:
            avg = np.mean([t['value'] for t in self.tick_history])
            return float(avg) if avg else 5.0
        
        try:
            values = np.array([t['value'] for t in list(self.tick_history)[-period:]], dtype=float)
            multiplier = 2 / (period + 1)
            ema = values[0]
            
            for value in values[1:]:
                ema = value * multiplier + ema * (1 - multiplier)
            
            return float(ema)
        except Exception as e:
            logger.warning(f"EMA calculation error: {e}")
            return 5.0
    
    def calculate_atr(self, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(self.tick_history) < period:
            return 1.0
        
        try:
            values = np.array([t['value'] for t in list(self.tick_history)[-period:]], dtype=float)
            atr = np.mean(np.abs(np.diff(values)))
            return float(atr) if atr > 0 else 1.0
        except Exception as e:
            logger.warning(f"ATR calculation error: {e}")
            return 1.0
    
    def predict_next_digit(self) -> Tuple[int, float, StrategyType]:
        """Predict next digit with confidence"""
        if len(self.tick_history) < 10:
            return 5, 50.0, StrategyType.MATCH
        
        try:
            recent_ticks = [t['value'] for t in list(self.tick_history)[-30:]]
            
            # Calculate indicators
            rsi = self.calculate_rsi(14)
            k_stoch, d_stoch = self.calculate_stochastic(14)
            ema = self.calculate_ema(20)
            atr = self.calculate_atr(14)
            
            # Digit analysis
            digit_counts = {}
            for digit in recent_ticks:
                digit_counts[digit] = digit_counts.get(digit, 0) + 1
            
            avg_value = np.mean(recent_ticks)
            
            # Predict based on indicators
            scores = {}
            for digit in range(10):
                score = 0
                
                # RSI contribution (weight: 0.25)
                if rsi > 70:
                    score += (10 - digit) * 0.25 if digit > 5 else digit * 0.25
                elif rsi < 30:
                    score += digit * 0.25 if digit < 5 else (10 - digit) * 0.25
                else:
                    score += abs(digit - int(avg_value)) * 0.25
                
                # Stochastic contribution (weight: 0.25)
                if k_stoch > 80:
                    score += (10 - digit) * 0.25 if digit > 5 else digit * 0.25
                elif k_stoch < 20:
                    score += digit * 0.25 if digit < 5 else (10 - digit) * 0.25
                else:
                    score += abs(digit - int(ema)) * 0.25
                
                # Pattern frequency (weight: 0.30)
                score += digit_counts.get(digit, 0) * 0.30
                
                # Volatility (weight: 0.20)
                score += (1 - min(atr / 5, 1)) * 0.20
                
                scores[digit] = score
            
            predicted = max(scores, key=scores.get)
            total_score = sum(scores.values())
            confidence = (scores[predicted] / total_score) * 100 if total_score > 0 else 50
            
            # Auto-switch strategy
            threshold = float(self.config.get('prediction_engine', 'auto_switch_threshold', 52)) / 100
            if self.win_rate < threshold and len(self.trade_history) > 5:
                self.current_strategy = StrategyType.DIFFER if self.current_strategy == StrategyType.MATCH else StrategyType.MATCH
                logger.info(f"⚡ Strategy auto-switched to: {self.current_strategy.value}")
            
            return predicted, float(confidence), self.current_strategy
        
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 5, 50.0, StrategyType.MATCH
    
    def record_trade_result(self, trade: Trade):
        """Record trade result"""
        try:
            self.trade_history.append(trade)
            
            if len(self.trade_history) > 0:
                wins = sum(1 for t in self.trade_history if t.status == "won")
                self.win_rate = wins / len(self.trade_history)
                logger.info(f"📊 Win rate: {self.win_rate*100:.2f}% ({wins}/{len(self.trade_history)})")
            
            if trade.status == "won":
                self.prediction_accuracy = self.prediction_accuracy * (1 - self.learning_rate) + self.learning_rate
            else:
                self.prediction_accuracy = self.prediction_accuracy * (1 - self.learning_rate)
        
        except Exception as e:
            logger.error(f"Error recording trade: {e}")


# ============================================================================
# API CLIENT
# ============================================================================

class DerivAPIClient:
    """Deriv API WebSocket client"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.endpoint = "wss://ws.binaryws.com/websockets/v3"
        self.ws = None
        self.request_id = 0
        self.responses = {}
        self.is_connected = False
        self.reconnect_count = 0
        self.max_reconnects = int(os.getenv('MAX_RECONNECTS', 5))
        self.lock = threading.Lock()
        logger.info("API client initialized")
    
    def connect(self):
        """Connect to Deriv API"""
        try:
            logger.info(f"🔗 Connecting to {self.endpoint}")
            self.ws = websocket.WebSocketApp(
                self.endpoint,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open,
                ping_interval=30,
                ping_timeout=10
            )
            
            ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            ws_thread.start()
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            self._attempt_reconnect()
    
    def _on_open(self, ws):
        """WebSocket opened"""
        logger.info("✅ WebSocket connected successfully")
        self.is_connected = True
        self.reconnect_count = 0
        self._authorize()
    
    def _on_message(self, ws, message):
        """Handle message"""
        try:
            data = json.loads(message)
            if 'req_id' in data:
                with self.lock:
                    self.responses[data['req_id']] = data
            
            if os.getenv('DEBUG_API_RESPONSES') == 'true':
                logger.debug(f"API: {data}")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON error: {e}")
        except Exception as e:
            logger.error(f"Message error: {e}")
    
    def _on_error(self, ws, error):
        """WebSocket error"""
        logger.error(f"❌ WebSocket error: {error}")
        self.is_connected = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket closed"""
        logger.warning(f"⚠️ WebSocket closed: {close_msg}")
        self.is_connected = False
        self._attempt_reconnect()
    
    def _attempt_reconnect(self):
        """Attempt reconnection"""
        if self.reconnect_count < self.max_reconnects:
            self.reconnect_count += 1
            delay = 2 ** self.reconnect_count
            logger.info(f"🔄 Reconnect attempt {self.reconnect_count}/{self.max_reconnects} in {delay}s")
            time.sleep(delay)
            self.connect()
        else:
            logger.error("❌ Max reconnection attempts reached")
    
    def _authorize(self):
        """Authorize with API token"""
        try:
            self.request_id += 1
            request = {
                "authorize": self.api_token,
                "req_id": self.request_id
            }
            self.ws.send(json.dumps(request))
            logger.info("🔐 Authorization request sent")
            
            time.sleep(1)
            response = self.responses.get(self.request_id)
            if response and 'authorize' in response:
                logger.info("✅ Authorization successful")
                return True
            else:
                logger.error("❌ Authorization failed")
                return False
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return False
    
    def get_account_balance(self) -> Optional[float]:
        """Get account balance"""
        try:
            self.request_id += 1
            request = {
                "balance": 1,
                "req_id": self.request_id
            }
            self.ws.send(json.dumps(request))
            
            time.sleep(0.5)
            response = self.responses.get(self.request_id)
            if response and 'balance' in response:
                balance = response['balance'].get('balance')
                logger.info(f"💰 Balance: ${balance}")
                return balance
            return None
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return None
    
    def subscribe_ticks(self, symbol: str) -> bool:
        """Subscribe to ticks"""
        try:
            self.request_id += 1
            request = {
                "ticks": symbol,
                "req_id": self.request_id
            }
            self.ws.send(json.dumps(request))
            logger.info(f"📡 Subscribed to {symbol}")
            return True
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            return False
    
    def place_trade(self, symbol: str, amount: float, duration: int, trade_type: str) -> Optional[str]:
        """Place trade"""
        try:
            if not self.is_connected:
                logger.error("Not connected")
                return None
            
            self.request_id += 1
            request = {
                "buy": 1,
                "subscribe": 1,
                "contract_type": trade_type,
                "currency": "USD",
                "amount": amount,
                "symbol": symbol,
                "duration": duration,
                "duration_unit": "s",
                "req_id": self.request_id
            }
            
            self.ws.send(json.dumps(request))
            logger.info(f"🎯 Trade: {symbol} {trade_type} ${amount}")
            
            time.sleep(1)
            response = self.responses.get(self.request_id)
            if response and 'buy' in response:
                trade_id = response['buy'].get('transaction_id')
                logger.info(f"✅ Trade placed: {trade_id}")
                return trade_id
            else:
                logger.warning("❌ Trade placement failed")
                return None
        except Exception as e:
            logger.error(f"Trade error: {e}")
            return None


# ============================================================================
# MAIN BOT
# ============================================================================

class DerivBot:
    """Main bot class"""
    
    def __init__(self, config_file: str = 'bot_config.xml'):
        try:
            self.config = ConfigManager(config_file)
            self.prediction_engine = PredictionEngine(self.config)
            
            # Get credentials
            api_token = os.getenv('DERIV_API_TOKEN')
            if not api_token:
                raise ValueError("❌ DERIV_API_TOKEN not set in .env")
            
            self.api_client = DerivAPIClient(api_token)
            self.active_trades = {}
            self.session_stats = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_profit': 0.0,
                'total_loss': 0.0,
                'start_time': datetime.now(),
                'max_drawdown': 0.0,
                'daily_profit': 0.0
            }
            
            logger.info("=" * 70)
            logger.info("🚀 DERIV BOT v2.0 - INITIALIZED SUCCESSFULLY")
            logger.info("=" * 70)
        
        except Exception as e:
            logger.error(f"❌ Init error: {e}")
            raise
    
    def check_trading_conditions(self) -> bool:
        """Check if trading allowed"""
        try:
            daily_loss_limit = float(self.config.get('trade_config', 'daily_loss_limit', 500))
            if self.session_stats['daily_profit'] < -daily_loss_limit:
                logger.warning("⛔ Daily loss limit reached")
                return False
            
            consecutive_loss_limit = int(self.config.get('trade_config', 'consecutive_loss_limit', 5))
            recent_trades = list(self.prediction_engine.trade_history)[-consecutive_loss_limit:]
            if len(recent_trades) == consecutive_loss_limit:
                if all(t.status == "lost" for t in recent_trades):
                    logger.warning("⛔ Consecutive loss limit reached")
                    return False
            
            if not self.check_trading_hours():
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Condition check error: {e}")
            return False
    
    def check_trading_hours(self) -> bool:
        """Check trading hours"""
        try:
            enabled = self.config.get('execution_schedule', 'enabled', True)
            if not enabled:
                return True
            
            now = datetime.now()
            day = now.strftime('%A').lower()
            
            if not self.config.get('execution_schedule', f'{day}', True):
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Hours check error: {e}")
            return True
    
    def save_session_stats(self):
        """Save stats"""
        try:
            stats = {
                **self.session_stats,
                'start_time': self.session_stats['start_time'].isoformat(),
                'win_rate': (self.session_stats['winning_trades'] / max(1, self.session_stats['total_trades'])) * 100,
                'roi': (self.session_stats['total_profit'] / max(1, abs(self.session_stats['total_loss']))) * 100 if self.session_stats['total_loss'] != 0 else 0
            }
            
            with open('logs/bot_session.json', 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def run(self):
        """Main bot loop"""
        try:
            logger.info("Starting trading bot...")
            
            self.api_client.connect()
            time.sleep(3)
            
            if not self.api_client.is_connected:
                raise ConnectionError("Failed to connect")
            
            symbol = self.config.get('trade_config', 'symbol', 'FRXUSDJPY')
            self.api_client.subscribe_ticks(symbol)
            
            iteration = 0
            while True:
                iteration += 1
                
                if not self.api_client.is_connected:
                    logger.warning("🔄 Reconnecting...")
                    self.api_client.connect()
                    time.sleep(3)
                    continue
                
                try:
                    if not self.check_trading_conditions():
                        logger.info("⏸️ Waiting for trading conditions...")
                        time.sleep(10)
                        continue
                    
                    if iteration % 60 == 0:
                        self.api_client.get_account_balance()
                    
                    predicted_digit, confidence, strategy = self.prediction_engine.predict_next_digit()
                    logger.info(f"🔮 Prediction: {predicted_digit} | Confidence: {confidence:.1f}% | Strategy: {strategy.value}")
                    
                    min_confidence = float(self.config.get('prediction_engine', 'confidence_threshold', 65))
                    if confidence >= min_confidence:
                        stake = float(self.config.get('trade_config', 'stake', 10))
                        duration = int(self.config.get('trade_config', 'duration_value', 60))
                        
                        trade_type = TradeType.DIGITS_DIFFER.value if strategy == StrategyType.DIFFER else TradeType.DIGITS_MATCH.value
                        
                        trade_id = self.api_client.place_trade(symbol, stake, duration, trade_type)
                        
                        if trade_id:
                            trade = Trade(
                                trade_id=trade_id,
                                symbol=symbol,
                                amount=stake,
                                direction=strategy.value,
                                entry_time=datetime.now(),
                                confidence=confidence
                            )
                            self.active_trades[trade_id] = trade
                            self.session_stats['total_trades'] += 1
                    
                    if iteration % 100 == 0:
                        self.save_session_stats()
                    
                    interval = int(self.config.get('prediction_engine', 'prediction_interval', 3000)) / 1000
                    time.sleep(interval)
                
                except Exception as e:
                    logger.error(f"Loop error: {e}")
                    time.sleep(5)
        
        except KeyboardInterrupt:
            logger.info("⏹️ Stopped by user")
            self.shutdown()
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            self.shutdown()
            raise
    
    def shutdown(self):
        """Shutdown"""
        try:
            logger.info("Shutting down...")
            self.save_session_stats()
            self.print_session_summary()
            if self.api_client.ws:
                self.api_client.ws.close()
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
    
    def print_session_summary(self):
        """Print summary"""
        try:
            duration = datetime.now() - self.session_stats['start_time']
            win_rate = (self.session_stats['winning_trades'] / max(1, self.session_stats['total_trades'])) * 100
            
            logger.info("\n" + "=" * 70)
            logger.info("📊 SESSION SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Duration: {duration}")
            logger.info(f"Total Trades: {self.session_stats['total_trades']}")
            logger.info(f"Winning: {self.session_stats['winning_trades']} | Losing: {self.session_stats['losing_trades']}")
            logger.info(f"Win Rate: {win_rate:.2f}%")
            logger.info(f"Profit: ${self.session_stats['total_profit']:.2f} | Loss: ${self.session_stats['total_loss']:.2f}")
            logger.info(f"Net: ${self.session_stats['total_profit'] - self.session_stats['total_loss']:.2f}")
            logger.info(f"Max Drawdown: {self.session_stats['max_drawdown']:.2f}%")
            logger.info("=" * 70 + "\n")
        except Exception as e:
            logger.error(f"Summary error: {e}")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    try:
        if not os.path.exists('.env'):
            logger.warning("Creating .env file...")
            with open('.env', 'w') as f:
                f.write("# Deriv Bot Configuration\n")
                f.write("DERIV_API_TOKEN=your_api_token_here\n")
                f.write("MAX_RECONNECTS=5\n")
                f.write("DEBUG_API_RESPONSES=false\n")
            logger.info("✅ .env file created - add your DERIV_API_TOKEN")
            return
        
        bot = DerivBot()
        bot.run()
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
