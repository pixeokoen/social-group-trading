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
        prompt = """You are a trading signal analyzer. Analyze the following message and determine if it contains trading signals.

Extract the following information if present:
1. Is this a trading signal? (yes/no)
2. Symbol/Ticker (e.g., AAPL, TSLA, SPY)
3. Action (BUY or SELL)
4. Entry Price (if specified)
5. Stop Loss (if specified)
6. Take Profit / Target (if specified)
7. Any additional remarks or context

Common patterns to look for:
- "Buy AAPL at 150"
- "TSLA: SELL @ 220, SL: 225, TP: 210"
- "Long MSFT 380, stop 375, target 390"
- "🚀 NVDA BUY 500 🎯 520 ⛔ 490"
- "Entry: GOOGL 140, Stop: 135, Target: 150"

Return the analysis in this exact JSON format:
{
    "is_signal": true/false,
    "signals": [
        {
            "symbol": "TICKER",
            "action": "BUY/SELL",
            "price": 150.00 or null,
            "stop_loss": 145.00 or null,
            "take_profit": 160.00 or null,
            "confidence": 0.95,
            "remarks": "Any additional context or notes"
        }
    ],
    "original_message": "The original message",
    "analysis_notes": "Explanation of why this is/isn't a signal"
}

If multiple signals are found in one message, include all of them in the signals array.
If no signal is found, return is_signal: false with empty signals array.

Message to analyze:
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for cost efficiency
                messages=[
                    {"role": "system", "content": "You are a precise trading signal analyzer. Always return valid JSON."},
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
                
            db_signal = {
                "symbol": symbol,
                "action": signal.get("action", "BUY").upper(),
                "price": signal.get("price"),
                "stop_loss": signal.get("stop_loss"),
                "take_profit": signal.get("take_profit"),
                "source": "message_paste",
                "original_message": analysis_result.get("original_message", ""),
                "remarks": signal.get("remarks", "") + f"\nConfidence: {signal.get('confidence', 'N/A')}",
                "analysis_notes": analysis_result.get("analysis_notes", "")
            }
            db_signals.append(db_signal)
            
        return db_signals

# Create a singleton instance
message_analyzer = MessageAnalyzer() if os.getenv("OPENAI_API_KEY") else None 