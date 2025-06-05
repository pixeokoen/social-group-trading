"""
Message Analyzer using OpenAI GPT
Analyzes messages to extract trading signals
"""
import os
import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class MessageAnalyzer:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)
        
    def analyze_message(self, message: str) -> Dict[str, Any]:
        """
        Analyze a message to extract trading signals using GPT-4
        Returns structured data about any trading signals found
        """
        prompt = """You are an expert trading signal analyzer with deep market knowledge. Analyze the following message and extract trading signals with precision.

CRITICAL: Pay close attention to KEYWORDS that indicate specific trading strategies:

BREAKOUT KEYWORDS (Use STOP orders):
- "break", "breakout", "breaking", "breakthrough" 
- "above resistance", "through resistance"
- "new high", "all-time high", "52-week high"
- "momentum", "explosive", "rocket", "moon"
- "breach", "clear", "punch through"

REVERSAL/SUPPORT KEYWORDS (Use LIMIT orders):
- "bounce", "support", "floor", "bottom"
- "reversal", "pivot", "turn", "dip buying"
- "oversold", "pullback", "retracement"
- "resistance", "ceiling", "rejection"

IMMEDIATE KEYWORDS (Use MARKET orders):
- "now", "immediately", "urgent", "asap"
- "market order", "at market"

ANALYSIS FRAMEWORK:
1. Symbol Recognition: Look for $TICKER, TICKER, or stock names
2. Action Detection: BUY/SELL/LONG/SHORT (default to BUY if bullish context)
3. Price Analysis: Look for entry prices with symbols like $, @, or price context
4. Strategy Detection: Use keywords above to determine entry concept
5. Order Type Logic: Map entry concept to appropriate order type
6. Risk Management: Find stop loss (🔴, SL, stop, below) and targets (✅, TP, target, above)

PATTERN EXAMPLES:
• "$APLD $12.70 (break)" → breakout strategy → STOP order
• "TSLA bounce at 220" → support bounce → LIMIT order  
• "Buy NVDA now at market" → immediate → MARKET order
• "AAPL pullback to 150" → mean reversion → LIMIT order

EMOJI MEANINGS:
🟢 = bullish signal/entry
🔴 = bearish/stop loss
✅ = take profit/targets
⚪️ = entry price/neutral
🚀 = momentum/breakout
⛔ = stop loss

Extract and return in this JSON format:
{
    "is_signal": true/false,
    "signals": [
        {
            "symbol": "TICKER",
            "action": "BUY/SELL", 
            "price": 12.70,
            "entry_concept": "breakout/support/resistance/momentum/reversal/pullback",
            "order_type": "STOP/LIMIT/MARKET/STOP_LIMIT",
            "stop_loss": 11.00,
            "take_profit_levels": [13.0, 13.2, 13.5, 14.0, 15.0],
            "time_frame": "swing/intraday/position",
            "confidence": 0.90,
            "conditions": "Break above $12.70 resistance",
            "remarks": "Multiple profit targets with clear breakout setup"
        }
    ],
    "original_message": "The original message",
    "analysis_notes": "Why this strategy was chosen and key indicators found"
}

CRITICAL RULES:
1. If you see "break", "breakout", or similar → entry_concept: "breakout" → order_type: "STOP"
2. If you see "bounce", "support", "dip" → entry_concept: "support" → order_type: "LIMIT"  
3. If you see "resistance", "ceiling" → entry_concept: "resistance" → order_type: "LIMIT"
4. Multiple price levels with / or , → take_profit_levels array
5. 🔴 or numbers below entry = stop loss
6. ✅ or numbers above entry = take profit
7. Always explain your reasoning in analysis_notes

Message to analyze:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
                messages=[
                    {"role": "system", "content": "You are a precise trading signal analyzer with deep market knowledge. Always return valid JSON with enhanced signal details."},
                    {"role": "user", "content": prompt + message}
                ],
                temperature=0.1,  # Low temperature for consistent results
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Ensure the response has the expected structure
            if "is_signal" not in result:
                result["is_signal"] = False
            if "signals" not in result:
                result["signals"] = []
            if "original_message" not in result:
                result["original_message"] = message
                
            # Validate and normalize signals
            for signal in result.get("signals", []):
                # Normalize action
                if signal.get("action") in ["LONG", "long"]:
                    signal["action"] = "BUY"
                elif signal.get("action") in ["SHORT", "short"]:
                    signal["action"] = "SELL"
                
                # Ensure take_profit_levels is always an array if present
                if "take_profit" in signal and signal["take_profit"] is not None:
                    # Handle legacy single take_profit field
                    if "take_profit_levels" not in signal:
                        signal["take_profit_levels"] = [signal["take_profit"]]
                    del signal["take_profit"]  # Remove old field
                
                # Enhanced order type determination based on keywords and entry concept
                if not signal.get("order_type"):
                    entry_concept = signal.get("entry_concept", "").lower()
                    original_msg = message.lower()
                    
                    # Check for breakout keywords in both entry concept and original message
                    breakout_keywords = ["break", "breakout", "breaking", "breakthrough", "momentum", "explosive", "rocket", "above resistance", "through resistance"]
                    support_keywords = ["bounce", "support", "floor", "bottom", "reversal", "pivot", "turn", "dip", "oversold", "pullback", "retracement"]
                    immediate_keywords = ["now", "immediately", "urgent", "asap", "market order", "at market"]
                    
                    # Check original message for keywords
                    has_breakout = any(keyword in original_msg for keyword in breakout_keywords)
                    has_support = any(keyword in original_msg for keyword in support_keywords)
                    has_immediate = any(keyword in original_msg for keyword in immediate_keywords)
                    
                    # Also check entry concept
                    concept_breakout = "breakout" in entry_concept or "momentum" in entry_concept
                    concept_support = any(word in entry_concept for word in ["support", "pivot", "reversal", "resistance", "pullback", "retracement"])
                    
                    # Priority order type determination
                    if has_immediate:
                        signal["order_type"] = "MARKET"
                    elif has_breakout or concept_breakout:
                        signal["order_type"] = "STOP"
                    elif has_support or concept_support:
                        signal["order_type"] = "LIMIT"
                    else:
                        signal["order_type"] = "MARKET"  # Conservative default
                
            return result
            
        except Exception as e:
            print(f"Error analyzing message with OpenAI: {e}")
            # Return a default response on error
            return {
                "is_signal": False,
                "signals": [],
                "original_message": message,
                "analysis_notes": f"Error during analysis: {str(e)}"
            }
    
    def extract_signals_for_db(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert the analysis result into a format ready for database insertion
        """
        if not analysis_result.get("is_signal") or not analysis_result.get("signals"):
            return []
        
        db_signals = []
        for signal in analysis_result["signals"]:
            # Ensure symbol is uppercase and clean
            symbol = signal.get("symbol", "").upper().strip()
            if not symbol:
                continue
            
            # Handle multiple take profit levels - use first one for legacy take_profit field
            take_profit_levels = signal.get("take_profit_levels", [])
            primary_take_profit = take_profit_levels[0] if take_profit_levels else signal.get("take_profit")
            
            # Build enhanced remarks with all new information
            remarks_parts = []
            if signal.get("remarks"):
                remarks_parts.append(signal.get("remarks"))
            if signal.get("entry_concept"):
                remarks_parts.append(f"Entry Concept: {signal.get('entry_concept')}")
            if signal.get("order_type"):
                remarks_parts.append(f"Recommended Order Type: {signal.get('order_type')}")
            if signal.get("time_frame"):
                remarks_parts.append(f"Time Frame: {signal.get('time_frame')}")
            if signal.get("conditions"):
                remarks_parts.append(f"Conditions: {signal.get('conditions')}")
            if signal.get("confidence"):
                remarks_parts.append(f"Confidence: {signal.get('confidence')}")
            if take_profit_levels and len(take_profit_levels) > 1:
                targets_str = ", ".join([f"${tp:.2f}" for tp in take_profit_levels])
                remarks_parts.append(f"Multiple Targets: {targets_str}")
                
            enhanced_remarks = " | ".join(remarks_parts)
                
            db_signal = {
                "symbol": symbol,
                "action": signal.get("action", "BUY").upper(),
                "price": signal.get("price"),
                "stop_loss": signal.get("stop_loss"),
                "take_profit": primary_take_profit,  # Use first target for legacy compatibility
                "source": "message_paste",
                "original_message": analysis_result.get("original_message", ""),
                "remarks": enhanced_remarks,
                "analysis_notes": analysis_result.get("analysis_notes", ""),
                # Store enhanced data in analysis_notes as JSON for future use
                "enhanced_data": {
                    "entry_concept": signal.get("entry_concept"),
                    "order_type": signal.get("order_type"),
                    "take_profit_levels": take_profit_levels,
                    "time_frame": signal.get("time_frame"),
                    "conditions": signal.get("conditions"),
                    "confidence": signal.get("confidence")
                }
            }
            db_signals.append(db_signal)
            
        return db_signals

# Create a singleton instance
message_analyzer = MessageAnalyzer() if os.getenv("OPENAI_API_KEY") else None 