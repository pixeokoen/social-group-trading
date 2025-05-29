import re
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SignalParser:
    """Parse trading signals from WhatsApp messages"""
    
    # Common trading signal patterns
    PATTERNS = {
        # Pattern: BUY AAPL @ 150, SL: 145, TP: 160
        'standard': re.compile(
            r'(?P<action>BUY|SELL|LONG|SHORT)\s+'
            r'(?P<symbol>[A-Z]{1,5})\s*'
            r'(?:@|at|AT)?\s*'
            r'(?P<price>\d+\.?\d*)?'
            r'(?:.*?SL[:\s]+(?P<stop_loss>\d+\.?\d*))?'
            r'(?:.*?TP[:\s]+(?P<take_profit>\d+\.?\d*))?',
            re.IGNORECASE
        ),
        # Pattern: AAPL: BUY @ 150
        'symbol_first': re.compile(
            r'(?P<symbol>[A-Z]{1,5})[:\s]+'
            r'(?P<action>BUY|SELL|LONG|SHORT)\s*'
            r'(?:@|at|AT)?\s*'
            r'(?P<price>\d+\.?\d*)?',
            re.IGNORECASE
        ),
        # Pattern: Entry: AAPL 150, Stop: 145, Target: 160
        'entry_format': re.compile(
            r'(?:ENTRY[:\s]+)?'
            r'(?P<symbol>[A-Z]{1,5})\s+'
            r'(?P<price>\d+\.?\d*)'
            r'(?:.*?STOP[:\s]+(?P<stop_loss>\d+\.?\d*))?'
            r'(?:.*?TARGET[:\s]+(?P<take_profit>\d+\.?\d*))?',
            re.IGNORECASE
        ),
        # Pattern: 🚀 AAPL BUY 150 🎯 160 ⛔ 145
        'emoji_format': re.compile(
            r'(?P<symbol>[A-Z]{1,5})\s+'
            r'(?P<action>BUY|SELL|LONG|SHORT)\s+'
            r'(?P<price>\d+\.?\d*)'
            r'(?:.*?🎯\s*(?P<take_profit>\d+\.?\d*))?'
            r'(?:.*?⛔\s*(?P<stop_loss>\d+\.?\d*))?',
            re.IGNORECASE
        )
    }
    
    # Keywords that indicate a trading signal
    SIGNAL_KEYWORDS = [
        'buy', 'sell', 'long', 'short', 'entry', 'position',
        'trade', 'alert', 'signal', 'setup', 'opportunity'
    ]
    
    # Keywords to exclude (noise)
    EXCLUDE_KEYWORDS = [
        'chat', 'hello', 'hi', 'thanks', 'good morning', 'gm',
        'how are', 'congrats', 'welcome', 'joined', 'left'
    ]
    
    # Valid US stock symbols (can be expanded)
    def is_valid_symbol(self, symbol: str) -> bool:
        """Check if the symbol is a valid US stock ticker"""
        if not symbol:
            return False
        
        # Basic validation: 1-5 uppercase letters
        if not re.match(r'^[A-Z]{1,5}$', symbol.upper()):
            return False
        
        # Could add additional validation here (e.g., check against a list of known symbols)
        return True
    
    def normalize_action(self, action: str) -> Optional[str]:
        """Normalize action to BUY or SELL"""
        action = action.upper()
        if action in ['BUY', 'LONG']:
            return 'BUY'
        elif action in ['SELL', 'SHORT']:
            return 'SELL'
        return None
    
    def should_process_message(self, message: str) -> bool:
        """Determine if a message should be processed for signals"""
        message_lower = message.lower()
        
        # Skip if message contains exclude keywords
        if any(keyword in message_lower for keyword in self.EXCLUDE_KEYWORDS):
            return False
        
        # Process if message contains signal keywords
        if any(keyword in message_lower for keyword in self.SIGNAL_KEYWORDS):
            return True
        
        # Process if message matches basic patterns (has stock-like symbols)
        if re.search(r'\b[A-Z]{1,5}\b', message):
            return True
        
        return False
    
    def parse_signal(self, message: str) -> Optional[Dict[str, Any]]:
        """Parse a trading signal from a WhatsApp message"""
        
        if not self.should_process_message(message):
            return None
        
        # Try each pattern
        for pattern_name, pattern in self.PATTERNS.items():
            match = pattern.search(message)
            if match:
                data = match.groupdict()
                
                # Extract and validate symbol
                symbol = data.get('symbol', '').upper()
                if not self.is_valid_symbol(symbol):
                    continue
                
                # Extract and normalize action
                action = self.normalize_action(data.get('action', ''))
                if not action:
                    # For entry_format pattern, default to BUY
                    if pattern_name == 'entry_format':
                        action = 'BUY'
                    else:
                        continue
                
                # Extract numeric values
                try:
                    price = float(data.get('price')) if data.get('price') else None
                    stop_loss = float(data.get('stop_loss')) if data.get('stop_loss') else None
                    take_profit = float(data.get('take_profit')) if data.get('take_profit') else None
                except (ValueError, TypeError):
                    continue
                
                # Return parsed signal
                signal = {
                    'symbol': symbol,
                    'action': action,
                    'price': price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'source': 'whatsapp',
                    'original_message': message,
                    'pattern_matched': pattern_name
                }
                
                logger.info(f"Parsed signal from WhatsApp: {signal}")
                return signal
        
        return None
    
    def parse_multiple_signals(self, message: str) -> List[Dict[str, Any]]:
        """Parse multiple signals from a single message"""
        signals = []
        
        # Split message by common delimiters
        lines = re.split(r'[\n;]|(?:\d+\))', message)
        
        for line in lines:
            signal = self.parse_signal(line.strip())
            if signal:
                signals.append(signal)
        
        return signals

# Singleton instance
signal_parser = SignalParser()

# Example usage and tests
if __name__ == "__main__":
    test_messages = [
        "BUY AAPL @ 150, SL: 145, TP: 160",
        "TSLA: SELL at 220",
        "🚀 MSFT BUY 380 🎯 400 ⛔ 370",
        "Entry: GOOGL 140, Stop: 135, Target: 150",
        "Good morning everyone!",  # Should be filtered out
        "LONG NVDA 500",
        "Alert: SHORT SPY @ 440 with stop loss at 445"
    ]
    
    parser = SignalParser()
    for msg in test_messages:
        result = parser.parse_signal(msg)
        if result:
            print(f"Message: {msg}")
            print(f"Parsed: {result}\n")
        else:
            print(f"Message: {msg} - No signal detected\n") 