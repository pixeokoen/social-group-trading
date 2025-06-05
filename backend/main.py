from fastapi import FastAPI, Depends, HTTPException, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime
import json
import hashlib
import hmac
import os
from decimal import Decimal, ROUND_DOWN
import secrets
import asyncio
from jose import JWTError, jwt
from contextlib import asynccontextmanager
from math import floor

from models import (
    Signal, Trade, User, SignalCreate, TradeCreate, 
    WHAPIWebhook, SignalApproval, TradeClose, WhatsAppMessage,
    MessageAnalysisRequest, MessageAnalysisResponse,
    Account, AccountCreate, AccountUpdate, UserSession,
    SignalSource, SignalSourceCreate, SignalSourceUpdate, SourceAccountMapping,
    UserCreate
)
from db import get_db_connection
from auth import get_current_user, create_access_token, authenticate_user, register
from alpaca_client import AlpacaClient
from signal_parser import signal_parser
from message_analyzer import message_analyzer

# Background task for auto-sync
async def auto_sync_trades():
    """Background task to sync trades every 30 seconds"""
    while True:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get all active accounts
            cursor.execute("""
                SELECT DISTINCT a.id, a.api_key, a.api_secret, a.account_type
                FROM accounts a
                JOIN trades t ON a.id = t.account_id
                WHERE a.is_active = TRUE 
                AND a.broker = 'alpaca'
                AND t.status IN ('pending', 'open')
            """)
            
            accounts = cursor.fetchall()
            
            for account in accounts:
                try:
                    # Get broker client
                    client = AlpacaClient(
                        api_key=account[1],
                        secret_key=account[2],
                        paper=(account[3] == 'paper')
                    )
                    
                    # Sync trades for this account - both pending and recently opened
                    cursor.execute("""
                        SELECT id, broker_order_id, symbol, status
                        FROM trades 
                        WHERE account_id = %s 
                        AND (
                            (status = 'pending' AND broker_order_id IS NOT NULL)
                            OR (status = 'filled' AND broker_order_id IS NOT NULL AND created_at > NOW() - INTERVAL '5 minutes')
                        )
                    """, (account[0],))
                    
                    pending_trades = cursor.fetchall()
                    
                    for trade in pending_trades:
                        try:
                            trade_id, broker_order_id, symbol, current_status = trade
                            
                            # Check if levels have already been processed for this trade
                            cursor.execute("""
                                SELECT COUNT(*) FROM take_profit_levels WHERE trade_id = %s
                                UNION ALL
                                SELECT COUNT(*) FROM stop_loss_levels WHERE trade_id = %s
                            """, (trade_id, trade_id))
                            level_counts = cursor.fetchall()
                            tp_count = level_counts[0][0] if level_counts else 0
                            sl_count = level_counts[1][0] if len(level_counts) > 1 else 0
                            
                            # Skip if BOTH take profit AND stop loss levels already exist
                            # (Don't skip if only one type exists - we might need to process the other)
                            if tp_count > 0 and sl_count > 0:
                                continue
                            
                            # Get order status from broker
                            order_status = await client.get_order_status(broker_order_id)
                            
                            # Process if order is filled OR if trade is already open (market orders)
                            should_process = False
                            fill_price = None
                            filled_qty = None
                            
                            if order_status and order_status['status'] == 'filled':
                                # Order just filled
                                fill_price = float(order_status.get('filled_avg_price', 0))
                                filled_qty = float(order_status.get('filled_qty', 0))
                                should_process = True
                                
                                if current_status == 'pending':
                                    # Update trade status
                                    cursor.execute("""
                                        UPDATE trades 
                                        SET status = 'filled',
                                            broker_fill_price = %s,
                                            entry_price = %s,
                                            quantity = %s,
                                            opened_at = %s
                                        WHERE id = %s
                                    """, (
                                        fill_price,
                                        fill_price,
                                        filled_qty,
                                        order_status.get('filled_at'),
                                        trade_id
                                    ))
                                    print(f"Auto-sync: Trade {symbol} filled at ${fill_price} - {filled_qty} shares")
                            
                            elif current_status == 'filled':
                                # Trade already open (market order), get current trade data
                                cursor.execute("""
                                    SELECT entry_price, quantity FROM trades WHERE id = %s
                                """, (trade_id,))
                                trade_data = cursor.fetchone()
                                if trade_data:
                                    fill_price = float(trade_data[0])
                                    filled_qty = float(trade_data[1])
                                    should_process = True
                                    print(f"Auto-sync: Processing levels for already-filled trade {symbol} at ${fill_price} - {filled_qty} shares")
                            
                            if should_process and fill_price and filled_qty:
                                # Get signal data for processing take profit and stop loss levels
                                cursor.execute("""
                                    SELECT s.* FROM signals s
                                    JOIN trades t ON t.signal_id = s.id
                                    WHERE t.id = %s
                                """, (trade_id,))
                                signal_data = cursor.fetchone()
                                
                                if signal_data:
                                    # Convert signal data to dict
                                    signal_dict = dict(zip([desc[0] for desc in cursor.description], signal_data))
                                    
                                    # Check for custom levels in trade_notifications
                                    cursor.execute("""
                                        SELECT data FROM trade_notifications 
                                        WHERE trade_id = %s AND data->>'notification_type' = 'custom_levels_pending'
                                        ORDER BY created_at DESC LIMIT 1
                                    """, (trade_id,))
                                    custom_levels_row = cursor.fetchone()
                                    custom_levels = None
                                    
                                    if custom_levels_row:
                                        notification_data = custom_levels_row[0]
                                        custom_levels = notification_data.get('custom_levels')
                                    
                                    # Process take profit and stop loss levels
                                    try:
                                        await process_trade_levels(trade_id, signal_dict, filled_qty, fill_price, cursor, custom_levels)
                                        print(f"✅ Successfully processed levels for trade {trade_id}")
                                    except Exception as level_error:
                                        print(f"❌ ERROR processing levels for trade {trade_id}: {level_error}")
                                        import traceback
                                        traceback.print_exc()
                        except Exception as e:
                            print(f"Error syncing trade {trade_id if 'trade_id' in locals() else 'unknown'}: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error syncing account {account[0]}: {e}")
            
            conn.commit()
            
            # NEW: Monitor and execute take profit/stop loss levels
            await monitor_and_execute_levels(conn)
            
            conn.close()
            
        except Exception as e:
            print(f"Error in auto-sync: {e}")
            if 'conn' in locals():
                conn.close()
        
        # Wait 2 seconds before next sync (much faster monitoring)
        await asyncio.sleep(2)

async def monitor_and_execute_levels(conn):
    """Monitor take profit and stop loss levels and execute them when prices hit"""
    try:
        cursor = conn.cursor()
        
        # Get all active levels grouped by account for efficient monitoring
        cursor.execute("""
            SELECT DISTINCT a.id, a.api_key, a.api_secret, a.account_type
            FROM accounts a
            WHERE a.is_active = TRUE 
            AND a.broker = 'alpaca'
            AND (
                EXISTS (
                    SELECT 1 FROM take_profit_levels tp 
                    JOIN trades t ON tp.trade_id = t.id 
                    WHERE t.account_id = a.id AND tp.status = 'pending' AND t.status = 'filled'
                )
                OR EXISTS (
                    SELECT 1 FROM stop_loss_levels sl 
                    JOIN trades t ON sl.trade_id = t.id 
                    WHERE t.account_id = a.id AND sl.status = 'active' AND t.status = 'filled'
                )
            )
        """)
        
        active_accounts = cursor.fetchall()
        
        for account in active_accounts:
            try:
                # Get broker client
                client = AlpacaClient(
                    api_key=account[1],
                    secret_key=account[2],
                    paper=(account[3] == 'paper')
                )
                
                # Get take profit levels for this account
                cursor.execute("""
                    SELECT 
                        tp.id, tp.trade_id, tp.level_number, tp.price, tp.shares_quantity,
                        t.symbol, t.action, t.user_id
                    FROM take_profit_levels tp
                    JOIN trades t ON tp.trade_id = t.id
                    WHERE t.account_id = %s 
                    AND tp.status = 'pending'
                    AND t.status = 'open'
                    ORDER BY t.symbol, tp.level_number
                """, (account[0],))
                
                tp_levels = cursor.fetchall()
                
                # Get stop loss levels for this account
                cursor.execute("""
                    SELECT 
                        sl.id, sl.trade_id, sl.price, t.symbol, t.action, t.user_id, t.quantity
                    FROM stop_loss_levels sl
                    JOIN trades t ON sl.trade_id = t.id
                    WHERE t.account_id = %s 
                    AND sl.status = 'active'
                    AND t.status = 'open'
                """, (account[0],))
                
                sl_levels = cursor.fetchall()
                
                # Group levels by symbol to minimize API calls
                symbols_to_check = set()
                levels_by_symbol = {}
                
                # Process take profit levels
                for tp in tp_levels:
                    symbol = tp[5]
                    symbols_to_check.add(symbol)
                    if symbol not in levels_by_symbol:
                        levels_by_symbol[symbol] = {'take_profit': [], 'stop_loss': []}
                    
                    levels_by_symbol[symbol]['take_profit'].append({
                        'id': tp[0],
                        'trade_id': tp[1],
                        'level_number': tp[2],
                        'price': float(tp[3]),
                        'shares': float(tp[4]),
                        'action': tp[6],
                        'user_id': tp[7]
                    })
                
                # Process stop loss levels
                for sl in sl_levels:
                    symbol = sl[3]
                    symbols_to_check.add(symbol)
                    if symbol not in levels_by_symbol:
                        levels_by_symbol[symbol] = {'take_profit': [], 'stop_loss': []}
                    
                    # Calculate remaining shares (total - executed take profits)
                    cursor.execute("""
                        SELECT COALESCE(SUM(shares_quantity), 0) 
                        FROM take_profit_levels 
                        WHERE trade_id = %s AND status = 'executed'
                    """, (sl[1],))
                    executed_tp_shares = cursor.fetchone()[0] or 0
                    remaining_shares = float(sl[6]) - float(executed_tp_shares)
                    
                    if remaining_shares > 0:
                        levels_by_symbol[symbol]['stop_loss'].append({
                            'id': sl[0],
                            'trade_id': sl[1],
                            'price': float(sl[2]),
                            'shares': remaining_shares,
                            'action': sl[4],
                            'user_id': sl[5]
                        })
                
                # Check prices and execute levels for each symbol
                for symbol, levels in levels_by_symbol.items():
                    try:
                        # Get current price
                        price_data = await client.get_latest_price(symbol)
                        if not price_data or 'price' not in price_data:
                            continue
                        
                        current_price = float(price_data['price'])
                        
                        # Check take profit levels
                        for tp_level in levels['take_profit']:
                            if should_execute_take_profit(tp_level, current_price):
                                await execute_level_as_market_order(client, tp_level, current_price, 'take_profit', cursor)
                        
                        # Check stop loss levels
                        for sl_level in levels['stop_loss']:
                            if should_execute_stop_loss(sl_level, current_price):
                                await execute_level_as_market_order(client, sl_level, current_price, 'stop_loss', cursor)
                    
                    except Exception as e:
                        print(f"Error checking {symbol} for account {account[0]}: {e}")
                        continue
            
            except Exception as e:
                print(f"Error monitoring account {account[0]}: {e}")
                continue
    
    except Exception as e:
        print(f"Error in level monitoring: {e}")

def should_execute_take_profit(level, current_price):
    """Check if take profit should be executed"""
    target_price = level['price']
    action = level['action']
    
    # Take profit: sell when price reaches or exceeds target (for long positions)
    if action.upper() == 'BUY':  # Long position
        return current_price >= target_price
    else:  # Short position
        return current_price <= target_price

def should_execute_stop_loss(level, current_price):
    """Check if stop loss should be executed"""
    target_price = level['price']
    action = level['action']
    
    # Stop loss: sell when price drops to or below target (for long positions)
    if action.upper() == 'BUY':  # Long position
        return current_price <= target_price
    else:  # Short position
        return current_price >= target_price

async def execute_level_as_market_order(client, level, current_price, level_type, cursor):
    """Execute a take profit or stop loss level as a market order"""
    try:
        # Get symbol from level or fetch from database
        if 'symbol' in level:
            symbol = level['symbol']
        else:
            cursor.execute("SELECT symbol FROM trades WHERE id = %s", (level['trade_id'],))
            symbol = cursor.fetchone()[0]
        
        shares = level['shares']
        level_id = level['id']
        trade_id = level['trade_id']
        original_action = level['action']
        
        # Determine execution action (opposite of original trade)
        execution_action = 'SELL' if original_action.upper() == 'BUY' else 'BUY'
        
        print(f"🎯 Executing {level_type} level {level_id}: {execution_action} {shares} {symbol} at ${current_price}")
        
        # Place market order for immediate execution
        order_result = await client.place_order(
            symbol=symbol,
            qty=shares,
            side=execution_action.lower(),
            type='market',
            time_in_force='day'
        )
        
        if order_result and 'id' in order_result:
            broker_order_id = order_result['id']
            
            # Update database with execution
            if level_type == 'take_profit':
                cursor.execute("""
                    UPDATE take_profit_levels 
                    SET status = 'executed',
                        executed_at = %s,
                        executed_price = %s,
                        broker_order_id = %s
                    WHERE id = %s
                """, (datetime.utcnow(), current_price, broker_order_id, level_id))
            
            elif level_type == 'stop_loss':
                cursor.execute("""
                    UPDATE stop_loss_levels 
                    SET status = 'executed',
                        executed_at = %s,
                        executed_price = %s,
                        executed_shares = %s,
                        broker_order_id = %s
                    WHERE id = %s
                """, (datetime.utcnow(), current_price, shares, broker_order_id, level_id))
            
            print(f"✅ {level_type.replace('_', ' ').title()} executed: {symbol} {shares} shares at ${current_price} (Order: {broker_order_id})")
            
            # TODO: Send notification to user
            return True
        else:
            print(f"❌ Failed to execute {level_type} level {level_id}: Invalid order result")
            return False
            
    except Exception as e:
        print(f"❌ Error executing {level_type} level {level_id}: {e}")
        return False

# Lifespan context manager for background tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting fast background trade monitoring (2s intervals)...")
    print("🔄 Trade fill detection: 2 seconds")
    print("🎯 Take profit/stop loss monitoring: 2 seconds") 
    task = asyncio.create_task(auto_sync_trades())
    
    yield
    
    # Shutdown
    print("Stopping background sync...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Trade Signal Filter & IBKR Execution API", lifespan=lifespan)

# Configure CORS for Vue frontend
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:4173",  # Vite preview port
]

# Add FRONTEND_URL from environment if set
frontend_url = os.getenv("FRONTEND_URL", "").strip()
if frontend_url:
    allowed_origins.append(frontend_url)
    # Also add without trailing slash
    if frontend_url.endswith("/"):
        allowed_origins.append(frontend_url[:-1])
    else:
        allowed_origins.append(frontend_url + "/")

# Add Render-specific URLs
allowed_origins.extend([
    "https://social-group-trading-frontend.onrender.com",
    "https://*.onrender.com",  # For Render preview deployments
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Webhook secret for WHAPI
WEBHOOK_SECRET = os.getenv("WHAPI_WEBHOOK_SECRET", "your-webhook-secret")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}  # user_id -> [connections]

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Connection might be closed
                    pass

    async def broadcast_to_user(self, data: dict, user_id: int):
        await self.send_personal_message(json.dumps(data), user_id)

manager = ConnectionManager()

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify WHAPI webhook signature"""
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

async def get_active_account(user: User) -> Optional[Account]:
    """Get the user's active trading account"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if user has an active account in session
        cursor.execute("""
            SELECT active_account_id FROM user_sessions WHERE user_id = %s
        """, (user.id,))
        session = cursor.fetchone()
        
        if session and session[0]:
            # Get the active account
            cursor.execute("""
                SELECT * FROM accounts WHERE id = %s AND user_id = %s AND is_active = TRUE
            """, (session[0], user.id))
        else:
            # Get the default account
            cursor.execute("""
                SELECT * FROM accounts WHERE user_id = %s AND is_default = TRUE AND is_active = TRUE
            """, (user.id,))
        
        account_data = cursor.fetchone()
        if account_data:
            columns = [desc[0] for desc in cursor.description]
            return Account(**dict(zip(columns, account_data)))
        
        return None
    finally:
        conn.close()

def get_broker_client(account: Account) -> Optional[AlpacaClient]:
    """Get broker client for the account"""
    if account.broker == "alpaca":
        return AlpacaClient(
            api_key=account.api_key,
            secret_key=account.api_secret,
            base_url=account.base_url,
            paper=(account.account_type == "paper")
        )
    # Add other brokers here in the future
    return None

def process_with_regex_parser(cursor, message_id, message_data, source_id, accounts_config):
    """Process message with regex parser for multiple accounts"""
    parsed_signals = signal_parser.parse_multiple_signals(message_data.get('text', ''))
    
    if parsed_signals:
        for account_config in accounts_config:
            account_id = account_config['account_id']
            auto_approve = account_config['auto_approve']
            user_id = account_config['user_id']
            
            for signal_data in parsed_signals:
                status = 'approved' if auto_approve else 'pending'
                
                cursor.execute("""
                    INSERT INTO signals (
                        whatsapp_message_id, symbol, action, price, 
                        stop_loss, take_profit, source, source_id,
                        original_message, status, account_id, user_id,
                        approved_by, approved_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    message_id,
                    signal_data['symbol'],
                    signal_data['action'],
                    signal_data.get('price'),
                    signal_data.get('stop_loss'),
                    signal_data.get('take_profit'),
                    'whatsapp',
                    source_id,
                    signal_data['original_message'],
                    status,
                    account_id if status == 'approved' else None,
                    user_id,
                    user_id if auto_approve else None,
                    datetime.utcnow() if auto_approve else None
                ))
        
        cursor.execute(
            "UPDATE whatsapp_messages SET is_signal = TRUE WHERE id = %s",
            (message_id,)
        )

@app.get("/")
async def root():
    return {"message": "Trade Signal Filter & IBKR Execution API", "version": "1.0.0"}

# WHAPI Webhook endpoint - now per source
@app.post("/api/webhook/whapi/{webhook_token}")
async def whapi_webhook_per_source(
    webhook_token: str,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """Receive WhatsApp messages for a specific source"""
    # Parse webhook data
    try:
        payload = await request.body()
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Look up source by webhook token
        cursor.execute("""
            SELECT ss.*, 
                   json_agg(
                       json_build_object(
                           'account_id', sa.account_id,
                           'auto_approve', sa.auto_approve,
                           'account_name', a.name,
                           'account_type', a.account_type,
                           'user_id', a.user_id
                       )
                   ) as accounts
            FROM signal_sources ss
            JOIN source_accounts sa ON ss.id = sa.source_id
            JOIN accounts a ON sa.account_id = a.id
            WHERE ss.webhook_token = %s
            AND ss.is_active = TRUE
            AND a.is_active = TRUE
            GROUP BY ss.id
        """, (webhook_token,))
        
        source_data = cursor.fetchone()
        
        if not source_data:
            # Log unknown webhook attempts
            cursor.execute("""
                INSERT INTO webhook_logs (instance_id, event_type, payload)
                VALUES (%s, %s, %s)
            """, (
                f"unknown-token-{webhook_token[:8]}",
                data.get('event', {}).get('type', ''),
                json.dumps(data)
            ))
            conn.commit()
            raise HTTPException(status_code=404, detail="Invalid webhook token")
        
        source_dict = dict(zip([desc[0] for desc in cursor.description], source_data))
        source_id = source_dict['id']
        filter_config = source_dict.get('filter_config', {})
        accounts_config = source_dict['accounts']
        
        # Log webhook for debugging
        cursor.execute("""
            INSERT INTO webhook_logs (instance_id, event_type, payload)
            VALUES (%s, %s, %s)
        """, (
            f"source-{source_id}",
            data.get('event', {}).get('type', ''),
            json.dumps(data)
        ))
        
        # Process message if it's a text message
        event = data.get('event', {})
        if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
            message_data = event.get('message', {})
            chat_data = event.get('chat', {})
            chat_id = chat_data.get('id', '')
            
            # Check chat_id filter if configured
            if filter_config.get('chat_id') and filter_config['chat_id'] != chat_id:
                # Message from different chat, ignore
                conn.commit()
                return {"status": "ignored", "reason": "chat_id mismatch"}
            
            # Store WhatsApp message
            cursor.execute("""
                INSERT INTO whatsapp_messages (raw_message, sender, group_name, timestamp, instance_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                message_data.get('text', ''),
                message_data.get('from', ''),
                chat_data.get('name', 'Unknown'),
                datetime.fromtimestamp(message_data.get('timestamp', 0)),
                f"chat-{chat_id}"
            ))
            
            message_id = cursor.fetchone()[0]
            
            # Process message with AI or regex parser
            signals_created = []
            if message_analyzer:
                try:
                    analysis_result = message_analyzer.analyze_message(message_data.get('text', ''))
                    
                    if analysis_result.get("is_signal"):
                        # Extract signals for database
                        db_signals = message_analyzer.extract_signals_for_db(analysis_result)
                        
                        # Create signals for each configured account
                        for account_config in accounts_config:
                            account_id = account_config['account_id']
                            auto_approve = account_config['auto_approve']
                            user_id = account_config['user_id']
                            
                            for signal_data in db_signals:
                                # Determine status based on auto_approve setting
                                status = 'approved' if auto_approve else 'pending'
                                
                                cursor.execute("""
                                    INSERT INTO signals (
                                        whatsapp_message_id, symbol, action, price, 
                                        stop_loss, take_profit, source, source_id,
                                        original_message, remarks, analysis_notes, 
                                        status, account_id, user_id, approved_by, approved_at
                                    )
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    RETURNING id
                                """, (
                                    message_id,
                                    signal_data['symbol'],
                                    signal_data['action'],
                                    signal_data.get('price'),
                                    signal_data.get('stop_loss'),
                                    signal_data.get('take_profit'),
                                    'whatsapp',
                                    source_id,
                                    signal_data.get('original_message', ''),
                                    signal_data.get('remarks', ''),
                                    signal_data.get('analysis_notes', ''),
                                    status,
                                    account_id if status == 'approved' else None,
                                    user_id,
                                    user_id if auto_approve else None,
                                    datetime.utcnow() if auto_approve else None
                                ))
                                
                                signal_id = cursor.fetchone()[0]
                                signals_created.append({
                                    'signal_id': signal_id,
                                    'account': account_config['account_name'],
                                    'status': status
                                })
                        
                        # Mark message as signal
                        cursor.execute(
                            "UPDATE whatsapp_messages SET is_signal = TRUE, processed = TRUE WHERE id = %s",
                            (message_id,)
                        )
                    else:
                        # Mark as processed but not a signal
                        cursor.execute(
                            "UPDATE whatsapp_messages SET processed = TRUE WHERE id = %s",
                            (message_id,)
                        )
                except Exception as e:
                    print(f"Error analyzing WhatsApp message: {e}")
                    # Fall back to regex parser
                    process_with_regex_parser(cursor, message_id, message_data, source_id, accounts_config)
            else:
                # No AI analyzer available, use regex parser
                process_with_regex_parser(cursor, message_id, message_data, source_id, accounts_config)
            
            print(f"Processed message for source '{source_dict['name']}' with {len(signals_created)} signals created")
        
        conn.commit()
        return {"status": "success", "message": "Webhook processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Keep the old webhook endpoint for backward compatibility but mark it as deprecated
@app.post("/api/webhook/whapi", deprecated=True)
async def whapi_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None)
):
    """[DEPRECATED] Legacy WHAPI webhook - use source-specific webhooks instead"""
    return {"status": "deprecated", "message": "Please use source-specific webhook URLs"}

# Signal endpoints
@app.get("/api/signals", response_model=List[Signal])
async def get_signals(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get trading signals - pending signals are shared, approved/executed are account-specific"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Pending signals are visible to all accounts
        # Approved/executed signals are filtered by account
        if status and status != 'pending':
            query = """
                SELECT s.*, u.username as approver_username
                FROM signals s
                LEFT JOIN users u ON s.approved_by = u.id
                WHERE s.status = %s AND s.account_id = %s
                ORDER BY s.created_at DESC
            """
            cursor.execute(query, (status, account.id))
        elif status == 'pending':
            query = """
                SELECT s.*, u.username as approver_username
                FROM signals s
                LEFT JOIN users u ON s.approved_by = u.id
                WHERE s.status = 'pending'
                ORDER BY s.created_at DESC
            """
            cursor.execute(query)
        else:
            # Show all signals: pending (no account filter) + account-specific approved/executed
            query = """
                SELECT s.*, u.username as approver_username
                FROM signals s
                LEFT JOIN users u ON s.approved_by = u.id
                WHERE s.status = 'pending' OR s.account_id = %s
                ORDER BY s.created_at DESC
            """
            cursor.execute(query, (account.id,))
        
        columns = [desc[0] for desc in cursor.description]
        signals = []
        
        for row in cursor.fetchall():
            signal_dict = dict(zip(columns, row))
            # Remove extra fields not in model
            signal_dict.pop('approver_username', None)
            signals.append(Signal(**signal_dict))
        
        return signals
    finally:
        conn.close()

@app.post("/api/signals", response_model=Signal)
async def create_signal(
    signal: SignalCreate, 
    current_user: User = Depends(get_current_user)
):
    """Create a new trading signal manually"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO signals (
                user_id, account_id, symbol, action, quantity, price, 
                stop_loss, take_profit, source, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'manual_entry', 'pending')
            RETURNING *
        """, (
            current_user.id, account.id, signal.symbol, signal.action, signal.quantity,
            signal.price, signal.stop_loss, signal.take_profit
        ))
        new_signal = cursor.fetchone()
        conn.commit()
        return Signal(**dict(zip([desc[0] for desc in cursor.description], new_signal)))
    finally:
        conn.close()

@app.post("/api/signals/{signal_id}/approve")
async def approve_signal(
    signal_id: int,
    approval: SignalApproval,
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a pending signal"""
    # Get active account if approving
    account = None
    if approval.approved:
        account = await get_active_account(current_user)
        if not account:
            raise HTTPException(status_code=400, detail="No active trading account")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if signal exists and is pending
        cursor.execute("SELECT status FROM signals WHERE id = %s", (signal_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Signal not found")
        if result[0] != 'pending':
            raise HTTPException(status_code=400, detail="Signal is not pending")
        
        # Update signal status
        new_status = 'approved' if approval.approved else 'rejected'
        
        if approval.approved and account:
            cursor.execute("""
                UPDATE signals 
                SET status = %s, approved_at = %s, approved_by = %s, account_id = %s
                WHERE id = %s
            """, (new_status, datetime.utcnow(), current_user.id, account.id, signal_id))
        else:
            cursor.execute("""
                UPDATE signals 
                SET status = %s, approved_at = %s, approved_by = %s
                WHERE id = %s
            """, (new_status, datetime.utcnow(), current_user.id, signal_id))
        
        conn.commit()
        return {"message": f"Signal {new_status}", "signal_id": signal_id}
    finally:
        conn.close()

@app.post("/api/signals/{signal_id}/validate-order")
async def validate_order(
    signal_id: int,
    order_params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Validate order parameters before execution"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get signal details
        cursor.execute("SELECT * FROM signals WHERE id = %s", (signal_id,))
        signal = cursor.fetchone()
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        signal_dict = dict(zip([desc[0] for desc in cursor.description], signal))
        
        # Extract order parameters
        quantity = order_params.get('quantity', signal_dict.get('quantity') or 100)
        order_type = order_params.get('order_type', 'MARKET')
        limit_price = order_params.get('limit_price')
        stop_price = order_params.get('stop_price')
        time_in_force = order_params.get('time_in_force', 'DAY')
        
        # Ensure quantity is a float for fractional shares
        quantity = float(quantity)
        
        # Get account info
        account_info = await broker_client.get_account_info()
        buying_power = account_info.get('buying_power', 0)
        
        # Get current market data
        market_data = await broker_client.get_market_data(signal_dict['symbol'])
        
        # Validate symbol exists
        if not market_data:
            return {
                "valid": False,
                "errors": ["Symbol not found or market data unavailable"],
                "symbol_info": None
            }
        
        # Calculate estimated cost based on order type
        if order_type == 'MARKET':
            estimated_price = market_data.get('last', 0)
        elif order_type == 'LIMIT':
            estimated_price = float(limit_price) if limit_price else market_data.get('last', 0)
        elif order_type == 'STOP':
            estimated_price = float(stop_price) if stop_price else market_data.get('last', 0)
        elif order_type == 'STOP_LIMIT':
            # For stop-limit, use limit price for cost estimation
            estimated_price = float(limit_price) if limit_price else market_data.get('last', 0)
        else:
            estimated_price = market_data.get('last', 0)
        
        estimated_cost = quantity * estimated_price
        
        # Check buying power
        has_sufficient_funds = estimated_cost <= buying_power
        
        # Prepare validation response
        validation_result = {
            "valid": has_sufficient_funds and market_data is not None,
            "errors": [],
            "warnings": [],
            "order_preview": {
                "symbol": signal_dict['symbol'],
                "action": signal_dict['action'],
                "quantity": quantity,
                "order_type": order_type,
                "limit_price": limit_price,
                "stop_price": stop_price,
                "time_in_force": time_in_force,
                "estimated_price": estimated_price,
                "estimated_cost": estimated_cost,
                "estimated_quantity": quantity
            },
            "account_info": {
                "buying_power": buying_power,
                "cash": account_info.get('cash', 0),
                "portfolio_value": account_info.get('portfolio_value', 0),
                "fractional_trading_enabled": account_info.get('fractional_trading', False)
            },
            "market_data": {
                "symbol": signal_dict['symbol'],
                "bid": market_data.get('bid', 0),
                "ask": market_data.get('ask', 0),
                "last": market_data.get('last', 0),
                "timestamp": str(market_data.get('timestamp', '')),
                "fractionable": market_data.get('fractionable', False)
            }
        }
        
        # Add errors/warnings
        if not has_sufficient_funds:
            validation_result["errors"].append(
                f"Insufficient buying power. Required: ${estimated_cost:.2f}, Available: ${buying_power:.2f}"
            )
        
        if order_type == 'LIMIT' and limit_price:
            if signal_dict['action'] == 'BUY' and float(limit_price) > market_data.get('ask', 0):
                validation_result["warnings"].append(
                    f"Limit price ${limit_price} is above current ask ${market_data.get('ask', 0):.2f}"
                )
            elif signal_dict['action'] == 'SELL' and float(limit_price) < market_data.get('bid', 0):
                validation_result["warnings"].append(
                    f"Limit price ${limit_price} is below current bid ${market_data.get('bid', 0):.2f}"
                )
        
        return validation_result
        
    finally:
        conn.close()

@app.post("/api/signals/validate-market-order")
async def validate_market_order(
    order_params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Validate a market order without requiring a signal ID"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    
    # Extract order parameters
    symbol = order_params.get('symbol', '').upper()
    action = order_params.get('action', 'BUY').upper()
    quantity = float(order_params.get('quantity', 0))
    order_type = order_params.get('order_type', 'MARKET').upper()
    limit_price = order_params.get('limit_price')
    stop_price = order_params.get('stop_price')
    
    errors = []
    warnings = []
    
    # Basic validation
    if not symbol:
        errors.append("Symbol is required")
    if quantity <= 0:
        errors.append("Quantity must be greater than 0")
    if order_type == 'LIMIT' and not limit_price:
        errors.append("Limit price is required for limit orders")
    if order_type == 'STOP' and not stop_price:
        errors.append("Stop price is required for stop orders")
    if order_type == 'STOP_LIMIT' and (not stop_price or not limit_price):
        errors.append("Both stop price and limit price are required for stop-limit orders")
    
    # Get market data
    market_data = None
    if symbol and not errors:
        try:
            market_data = await broker_client.get_market_data(symbol)
            if not market_data:
                errors.append(f"Could not fetch market data for {symbol}")
        except Exception as e:
            errors.append(f"Error fetching market data: {str(e)}")
    
    # Get account info
    account_info = None
    try:
        account_info = await broker_client.get_account_info()
    except Exception as e:
        warnings.append(f"Could not fetch account info: {str(e)}")
    
    # Calculate order preview
    order_preview = None
    if market_data and not errors:
        if order_type == 'MARKET':
            estimated_price = market_data['ask'] if action == 'BUY' else market_data['bid']
        elif order_type == 'LIMIT':
            estimated_price = float(limit_price)
        elif order_type == 'STOP':
            estimated_price = float(stop_price)
        elif order_type == 'STOP_LIMIT':
            # For stop-limit, use limit price for cost estimation
            estimated_price = float(limit_price)
        else:
            estimated_price = market_data['last']
        
        estimated_cost = quantity * estimated_price
        
        order_preview = {
            'estimated_quantity': quantity,
            'estimated_price': estimated_price,
            'estimated_cost': estimated_cost
        }
        
        # Check buying power
        if account_info and action == 'BUY':
            buying_power = account_info.get('buying_power', 0)
            if estimated_cost > buying_power:
                errors.append(f"Insufficient buying power. Required: ${estimated_cost:.2f}, Available: ${buying_power:.2f}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'market_data': market_data,
        'account_info': account_info,
        'order_preview': order_preview
    }

@app.post("/api/signals/analyze", response_model=MessageAnalysisResponse)
async def analyze_message(
    request: MessageAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze a message to extract trading signals using AI"""
    if not message_analyzer:
        raise HTTPException(
            status_code=503, 
            detail="Message analysis service not available. Please configure OPENAI_API_KEY."
        )
    
    try:
        # Analyze the message
        analysis_result = message_analyzer.analyze_message(request.message)
        
        # Return analysis result WITHOUT creating signals automatically
        # User will select which signals to create via separate endpoint
        return MessageAnalysisResponse(**analysis_result)
        
    except Exception as e:
        print(f"Error analyzing message: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/signals/create-from-analysis")
async def create_signals_from_analysis(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create signals from user-selected analysis results"""
    try:
        signals_data = request.get('signals', [])
        if not signals_data:
            raise HTTPException(status_code=400, detail="No signals provided")
        
        conn = get_db_connection()
        created_signals = []
        
        try:
            cursor = conn.cursor()
            
            for signal_data in signals_data:
                # Extract signal fields
                symbol = signal_data.get('symbol', '').upper()
                action = signal_data.get('action', 'BUY').upper()
                price = signal_data.get('entry_price') or signal_data.get('price')
                stop_loss = signal_data.get('stop_loss')
                take_profit = signal_data.get('take_profit')
                quantity = signal_data.get('quantity')
                original_message = signal_data.get('original_message', '')
                analysis_notes = signal_data.get('analysis_notes', '')
                
                # Extract enhanced data for info button
                enhanced_data = signal_data.get('enhanced_data', {})
                if not enhanced_data:
                    # Build enhanced data from signal analysis
                    enhanced_data = {
                        'entry_concept': signal_data.get('entry_concept'),
                        'order_type': signal_data.get('order_type'),
                        'take_profit_levels': signal_data.get('take_profit_levels', []),
                        'time_frame': signal_data.get('time_frame'),
                        'conditions': signal_data.get('conditions'),
                        'confidence': signal_data.get('confidence'),
                        'remarks': signal_data.get('remarks')
                    }
                
                # Validate required fields
                if not symbol or action not in ['BUY', 'SELL']:
                    continue  # Skip invalid signals
                
                cursor.execute("""
                    INSERT INTO signals (
                        user_id, symbol, action, price, 
                        stop_loss, take_profit, quantity, source, 
                        original_message, remarks, analysis_notes, status, enhanced_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
                    RETURNING id, symbol, action, price, stop_loss, take_profit, quantity, status, created_at
                """, (
                    current_user.id,
                    symbol,
                    action,
                    price,
                    stop_loss,
                    take_profit,
                    quantity,
                    'message_paste',  # Changed to message_paste to show info button
                    original_message,
                    '',  # remarks
                    analysis_notes,
                    json.dumps(enhanced_data)  # Store as JSON
                ))
                
                result = cursor.fetchone()
                if result:
                    signal_dict = dict(zip([desc[0] for desc in cursor.description], result))
                    created_signals.append(signal_dict)
                    print(f"Created signal {result[0]} for {symbol} {action}")
            
            conn.commit()
            
            return {
                "success": True,
                "created_count": len(created_signals),
                "signals": created_signals
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
        
    except Exception as e:
        print(f"Error creating signals from analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create signals: {str(e)}")

# Trade endpoints
@app.get("/api/trades", response_model=List[Trade])
async def get_trades(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all trades for the current user and active account
    
    NOTE: Trades are ALWAYS loaded from the local database, not from the broker.
    The sync process updates the database, then this endpoint serves that data.
    This ensures fast response times and works even if the broker API is down.
    """
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Load trades from LOCAL DATABASE (not from Alpaca)
        query = """
            SELECT *, link_group_id FROM trades 
            WHERE user_id = %s AND account_id = %s
        """
        params = [current_user.id, account.id]
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        
        trades = cursor.fetchall()
        trades_list = []
        
        for trade in trades:
            trade_dict = dict(zip([desc[0] for desc in cursor.description], trade))
            
            # Normalize action field to uppercase
            if 'action' in trade_dict and trade_dict['action']:
                trade_dict['action'] = trade_dict['action'].upper()
                # Handle any variations
                if trade_dict['action'] not in ['BUY', 'SELL']:
                    # Try to map common variations
                    if trade_dict['action'] in ['LONG', 'BTO', 'BUY_TO_OPEN']:
                        trade_dict['action'] = 'BUY'
                    elif trade_dict['action'] in ['SHORT', 'STO', 'SELL_TO_OPEN', 'STC', 'SELL_TO_CLOSE']:
                        trade_dict['action'] = 'SELL'
                    else:
                        # Default to BUY if we can't determine
                        print(f"Warning: Unknown action '{trade_dict['action']}' for trade {trade_dict.get('id', 'unknown')}, defaulting to BUY")
                        trade_dict['action'] = 'BUY'
            
            # Convert Decimal to float for JSON serialization
            for field in ['quantity', 'entry_price', 'exit_price', 'current_price', 'pnl', 
                          'floating_pnl', 'broker_fill_price', 'stop_loss', 'take_profit']:
                if field in trade_dict and trade_dict[field] is not None:
                    try:
                        trade_dict[field] = float(trade_dict[field])
                    except (ValueError, TypeError):
                        # If conversion fails, set sensible defaults
                        if field == 'quantity':
                            trade_dict[field] = 0.0
                        else:
                            trade_dict[field] = None
            
            # Handle potentially missing or null fields with defaults
            trade_dict['broker_order_id'] = trade_dict.get('broker_order_id') or ''
            trade_dict['signal_id'] = trade_dict.get('signal_id')
            trade_dict['close_reason'] = trade_dict.get('close_reason') or ''
            
            # Convert legacy 'open' status to 'filled' for compatibility
            if trade_dict.get('status') == 'open':
                trade_dict['status'] = 'filled'
            
            # Fetch take profit and stop loss levels for this trade
            trade_id = trade_dict['id']
            
            # Get take profit levels
            cursor.execute("""
                SELECT id, level_number, price, percentage, shares_quantity, status, executed_at, executed_price
                FROM take_profit_levels 
                WHERE trade_id = %s 
                ORDER BY level_number
            """, (trade_id,))
            tp_levels = cursor.fetchall()
            trade_dict['take_profit_levels'] = []
            
            for tp in tp_levels:
                trade_dict['take_profit_levels'].append({
                    'id': tp[0],
                    'level_number': tp[1],
                    'price': float(tp[2]) if tp[2] else 0,
                    'percentage': float(tp[3]) if tp[3] else 0,
                    'shares_quantity': float(tp[4]) if tp[4] else 0,
                    'status': tp[5],
                    'executed_at': tp[6],
                    'executed_price': float(tp[7]) if tp[7] else None
                })
            
            # Get stop loss levels
            cursor.execute("""
                SELECT id, price, status, executed_at, executed_price, executed_shares
                FROM stop_loss_levels 
                WHERE trade_id = %s 
                ORDER BY created_at DESC
                LIMIT 1
            """, (trade_id,))
            sl_level = cursor.fetchone()
            
            if sl_level:
                trade_dict['stop_loss'] = float(sl_level[1]) if sl_level[1] else None
                trade_dict['stop_loss_status'] = sl_level[2]
                trade_dict['stop_loss_executed_at'] = sl_level[3]
                trade_dict['stop_loss_executed_price'] = float(sl_level[4]) if sl_level[4] else None
            
            trades_list.append(Trade(**trade_dict))
        
        return trades_list
    finally:
        conn.close()

@app.post("/api/trades/execute/{signal_id}")
async def execute_trade(
    signal_id: int,
    order_params: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """Execute a trade based on an approved signal"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client for the account
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get signal details
        cursor.execute("SELECT * FROM signals WHERE id = %s", (signal_id,))
        signal = cursor.fetchone()
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        signal_dict = dict(zip([desc[0] for desc in cursor.description], signal))
        
        # Check if signal is approved
        if signal_dict['status'] != 'approved':
            raise HTTPException(status_code=400, detail="Signal must be approved before execution")
        
        # Extract order parameters
        if order_params:
            quantity = order_params.get('quantity', signal_dict.get('quantity') or 100)
            order_type = order_params.get('order_type', 'MARKET')
            limit_price = order_params.get('limit_price')
            stop_price = order_params.get('stop_price')
            time_in_force = order_params.get('time_in_force', 'DAY')
            custom_take_profit_levels = order_params.get('take_profit_levels', [])
            custom_stop_loss_price = order_params.get('stop_loss_price')
        else:
            quantity = signal_dict.get('quantity') or 100
            order_type = 'LMT' if signal_dict.get('price') else 'MKT'
            limit_price = float(signal_dict['price']) if signal_dict.get('price') else None
            stop_price = float(signal_dict['stop_price']) if signal_dict.get('stop_price') else None
            time_in_force = 'DAY'
            custom_take_profit_levels = []
            custom_stop_loss_price = None
        
        # Ensure quantity is a float for fractional shares
        quantity = float(quantity)
        
        # Convert order type to Alpaca format
        alpaca_order_type = order_type.lower()
        if order_type in ['LIMIT', 'LMT']:
            alpaca_order_type = 'limit'
        elif order_type in ['MARKET', 'MKT']:
            alpaca_order_type = 'market'
        elif order_type == 'STOP':
            alpaca_order_type = 'stop'
        elif order_type == 'STOP_LIMIT':
            alpaca_order_type = 'stop_limit'
        
        # Validate with broker (check account balance, etc.)
        account_summary = await broker_client.get_account_summary()
        buying_power = account_summary.get('BuyingPower', 0)
        
        # Calculate required capital (simplified)
        if alpaca_order_type == 'market':
            # Get current market price for validation
            market_data = await broker_client.get_market_data(signal_dict['symbol'])
            estimated_price = market_data.get('last', 0)
        elif alpaca_order_type == 'limit':
            estimated_price = float(limit_price) if limit_price else 0
        elif alpaca_order_type == 'stop':
            estimated_price = float(stop_price) if stop_price else 0
        elif alpaca_order_type == 'stop_limit':
            # For stop-limit, use limit price for cost estimation
            estimated_price = float(limit_price) if limit_price else 0
        else:
            estimated_price = 0
        
        required_capital = quantity * estimated_price
        
        if required_capital > buying_power:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient buying power. Required: ${required_capital:.2f}, Available: ${buying_power:.2f}"
            )
        
        # Execute trade via broker
        order_id = await broker_client.place_order(
            symbol=signal_dict['symbol'],
            action=signal_dict['action'],
            quantity=quantity,
            order_type=alpaca_order_type,
            limit_price=float(limit_price) if limit_price else None,
            stop_price=float(stop_price) if stop_price else None,
            time_in_force=time_in_force.lower()
        )
        
        if not order_id:
            raise HTTPException(status_code=500, detail="Failed to place order with broker")
        
        # Record trade in database with account_id
        cursor.execute("""
            INSERT INTO trades (
                user_id, account_id, signal_id, symbol, action, quantity, 
                entry_price, status, broker_order_id, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s)
            RETURNING id
        """, (
            current_user.id, account.id, signal_id, signal_dict['symbol'], 
            signal_dict['action'], quantity,
            limit_price or estimated_price or 0, str(order_id), datetime.utcnow()
        ))
        
        trade_id = cursor.fetchone()[0]
        
        # Update signal status and add account_id
        cursor.execute(
            "UPDATE signals SET status = 'executed', account_id = %s WHERE id = %s",
            (account.id, signal_id)
        )
        
        # If custom take profit/stop loss levels were provided, store them for later processing
        if custom_take_profit_levels or custom_stop_loss_price:
            custom_levels_data = {
                'take_profit_levels': custom_take_profit_levels,
                'stop_loss_price': custom_stop_loss_price
            }
            
            # Store custom levels in trade_notifications for processing when order fills
            cursor.execute("""
                INSERT INTO trade_notifications (
                    user_id, trade_id, data, created_at
                )
                VALUES (%s, %s, %s, %s)
            """, (
                current_user.id, trade_id, 
                json.dumps({
                    'notification_type': 'custom_levels_pending',
                    'custom_levels': custom_levels_data
                }),
                datetime.utcnow()
            ))
        
        conn.commit()
        
        # Send real-time notification
        await notify_trade_update(current_user.id, {
            "trade_id": trade_id,
            "symbol": signal_dict['symbol'],
            "action": signal_dict['action'],
            "quantity": quantity,
            "status": "pending",
            "message": "Order submitted to broker"
        })
        
        return {
            "message": "Trade executed successfully",
            "trade_id": trade_id,
            "broker_order_id": str(order_id),  # Ensure it's a string in response
            "account": account.name
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
        print(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/trades/close-position")
async def close_position(
    close_params: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Close or partially close a position with proper P&L tracking"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    
    symbol = close_params.get('symbol')
    quantity_to_close = float(close_params.get('quantity', 0))
    order_type = close_params.get('order_type', 'MARKET')
    limit_price = close_params.get('limit_price')
    stop_price = close_params.get('stop_price')
    
    if not symbol or quantity_to_close <= 0:
        raise HTTPException(status_code=400, detail="Invalid symbol or quantity")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get all open BUY trades for this symbol (FIFO - First In First Out)
        cursor.execute("""
            SELECT id, quantity, entry_price, broker_fill_price
            FROM trades 
            WHERE user_id = %s 
            AND account_id = %s 
            AND symbol = %s 
            AND action = 'BUY' 
            AND status = 'open'
            ORDER BY created_at ASC
        """, (current_user.id, account.id, symbol))
        
        open_positions = cursor.fetchall()
        
        if not open_positions:
            raise HTTPException(status_code=400, detail=f"No open positions found for {symbol}")
        
        # Calculate total open quantity
        total_open_quantity = sum(float(pos[1]) for pos in open_positions)
        
        if quantity_to_close > total_open_quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot close {quantity_to_close} shares. Only {total_open_quantity} shares available."
            )
        
        # Place the sell order
        alpaca_order_type = order_type.lower()
        if order_type == 'LIMIT':
            alpaca_order_type = 'limit'
        elif order_type == 'MARKET':
            alpaca_order_type = 'market'
        elif order_type == 'STOP':
            alpaca_order_type = 'stop'
        elif order_type == 'STOP_LIMIT':
            alpaca_order_type = 'stop_limit'
        
        order_id = await broker_client.place_order(
            symbol=symbol,
            action='SELL',
            quantity=quantity_to_close,
            order_type=alpaca_order_type,
            limit_price=float(limit_price) if limit_price else None,
            stop_price=float(stop_price) if stop_price else None
        )
        
        if not order_id:
            raise HTTPException(status_code=500, detail="Failed to place sell order")
        
        # Create a SELL trade record
        cursor.execute("""
            INSERT INTO trades (
                user_id, account_id, symbol, action, quantity,
                entry_price, status, broker_order_id, created_at
            )
            VALUES (%s, %s, %s, 'SELL', %s, %s, 'pending', %s, %s)
            RETURNING id
        """, (
            current_user.id, account.id, symbol, quantity_to_close,
            limit_price or 0, str(order_id), datetime.utcnow()
        ))
        
        sell_trade_id = cursor.fetchone()[0]
        
        # Track which positions are being closed (for P&L calculation later)
        remaining_to_close = quantity_to_close
        positions_to_update = []
        
        for pos_id, pos_quantity, entry_price, fill_price in open_positions:
            if remaining_to_close <= 0:
                break
                
            pos_quantity = float(pos_quantity)
            close_quantity = min(remaining_to_close, pos_quantity)
            
            positions_to_update.append({
                'id': pos_id,
                'close_quantity': close_quantity,
                'remaining_quantity': pos_quantity - close_quantity,
                'entry_price': float(fill_price or entry_price)
            })
            
            remaining_to_close -= close_quantity
        
        # Store the position closing info in a JSON field for later P&L calculation
        # We'll store the type info inside the JSON data itself to avoid column name issues
        cursor.execute("""
            INSERT INTO trade_notifications (
                user_id, trade_id, data, created_at
            )
            VALUES (%s, %s, %s, %s)
        """, (
            current_user.id, sell_trade_id, 
            json.dumps({
                'notification_type': 'position_close_pending',  # Store type in JSON
                'positions_to_close': positions_to_update,
                'total_quantity': quantity_to_close
            }),
            datetime.utcnow()
        ))
        
        conn.commit()
        
        # Send real-time notification
        await notify_trade_update(current_user.id, {
            "trade_id": sell_trade_id,
            "symbol": symbol,
            "action": "SELL",
            "quantity": quantity_to_close,
            "status": "pending",
            "message": f"Closing {quantity_to_close} shares of {symbol}"
        })
        
        return {
            "message": "Position close order submitted",
            "trade_id": sell_trade_id,
            "broker_order_id": str(order_id),
            "quantity_closed": quantity_to_close,
            "positions_affected": len(positions_to_update)
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/trades/{trade_id}/close")
async def close_trade(
    trade_id: int,
    close_data: TradeClose,
    current_user: User = Depends(get_current_user)
):
    """Close an open trade"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client for the account
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get trade details - ensure it belongs to the current account
        cursor.execute(
            "SELECT * FROM trades WHERE id = %s AND user_id = %s AND account_id = %s",
            (trade_id, current_user.id, account.id)
        )
        trade = cursor.fetchone()
        
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found in current account")
        
        trade_dict = dict(zip([desc[0] for desc in cursor.description], trade))
        
        if trade_dict['status'] != 'open':
            raise HTTPException(status_code=400, detail="Trade is not open")
        
        # Place closing order with broker
        close_action = 'SELL' if trade_dict['action'] == 'BUY' else 'BUY'
        close_order_id = await broker_client.place_order(
            symbol=trade_dict['symbol'],
            action=close_action,
            quantity=trade_dict['quantity'],
            order_type='MKT'  # Market order for closing
        )
        
        if not close_order_id:
            raise HTTPException(status_code=500, detail="Failed to place closing order")
        
        # Calculate P&L
        exit_price = close_data.close_price or trade_dict.get('current_price', trade_dict['entry_price'])
        
        if trade_dict['action'] == 'BUY':
            pnl = (float(exit_price) - float(trade_dict['entry_price'])) * trade_dict['quantity']
        else:
            pnl = (float(trade_dict['entry_price']) - float(exit_price)) * trade_dict['quantity']
        
        # Update trade
        cursor.execute("""
            UPDATE trades 
            SET status = 'closed', exit_price = %s, pnl = %s, 
                closed_at = %s, close_reason = %s
            WHERE id = %s
        """, (
            exit_price, pnl, datetime.utcnow(), 
            close_data.reason or 'Manual close', trade_id
        ))
        
        conn.commit()
        
        return {
            "message": "Trade closed successfully",
            "pnl": pnl,
            "exit_price": exit_price
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/trades/{trade_id}/update-price")
async def update_trade_price(
    trade_id: int,
    current_user: User = Depends(get_current_user)
):
    """Update current price and floating P&L for a trade"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client for the account
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get trade details - ensure it belongs to the current account
        cursor.execute(
            "SELECT * FROM trades WHERE id = %s AND user_id = %s AND account_id = %s AND status = 'open'",
            (trade_id, current_user.id, account.id)
        )
        trade = cursor.fetchone()
        
        if not trade:
            raise HTTPException(status_code=404, detail="Open trade not found in current account")
        
        trade_dict = dict(zip([desc[0] for desc in cursor.description], trade))
        
        # Get current market price from broker
        market_data = await broker_client.get_market_data(trade_dict['symbol'])
        current_price = market_data.get('last') or market_data.get('close')
        
        if not current_price:
            raise HTTPException(status_code=500, detail="Could not get current price")
        
        # Calculate floating P&L
        if trade_dict['action'] == 'BUY':
            floating_pnl = (float(current_price) - float(trade_dict['entry_price'])) * trade_dict['quantity']
        else:
            floating_pnl = (float(trade_dict['entry_price']) - float(current_price)) * trade_dict['quantity']
        
        # Update trade
        cursor.execute("""
            UPDATE trades 
            SET current_price = %s, floating_pnl = %s
            WHERE id = %s
        """, (current_price, floating_pnl, trade_id))
        
        conn.commit()
        
        return {
            "current_price": current_price,
            "floating_pnl": floating_pnl
        }
        
    finally:
        conn.close()

# Analytics endpoint
@app.get("/api/analytics")
async def get_analytics(current_user: User = Depends(get_current_user)):
    """Get comprehensive trading analytics for the current user and active account"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get account-level metrics
        cursor.execute("""
            SELECT realized_pnl, realized_pnl_updated_at, win_rate
            FROM accounts
            WHERE id = %s
        """, (account.id,))
        account_metrics = cursor.fetchone()
        
        # Trading statistics for the active account
        # Include all trades (open, closed, pending) for total count
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_trades,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_trades,
                COUNT(CASE WHEN action = 'SELL' AND status = 'closed' AND pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN action = 'SELL' AND status = 'closed' AND pnl < 0 THEN 1 END) as losing_trades,
                COALESCE(SUM(CASE WHEN action = 'SELL' AND status = 'closed' THEN pnl ELSE 0 END), 0) as total_pnl,
                COALESCE(AVG(CASE WHEN action = 'SELL' AND status = 'closed' THEN pnl ELSE NULL END), 0) as avg_pnl,
                AVG(CASE WHEN status = 'closed' THEN EXTRACT(EPOCH FROM (closed_at - opened_at))/3600 ELSE NULL END) as avg_trade_duration_hours,
                COALESCE(SUM(CASE WHEN status = 'open' THEN floating_pnl ELSE 0 END), 0) as total_floating_pnl
            FROM trades 
            WHERE user_id = %s AND account_id = %s
        """, (current_user.id, account.id))
        trade_stats = cursor.fetchone()
        
        # Signal statistics
        # Count all pending signals (not filtered by account since they're not assigned yet)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_signals,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_signals,
                COUNT(CASE WHEN status = 'approved' AND account_id = %s THEN 1 END) as approved_signals,
                COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_signals,
                COUNT(CASE WHEN status = 'executed' AND account_id = %s THEN 1 END) as executed_signals
            FROM signals
            WHERE status = 'pending' OR account_id = %s OR (approved_by = %s)
        """, (account.id, account.id, account.id, current_user.id))
        signal_stats = cursor.fetchone()
        
        # Get recent trades for the dashboard
        cursor.execute("""
            SELECT id, symbol, action, quantity, entry_price, current_price, 
                   floating_pnl, pnl, status, created_at
            FROM trades 
            WHERE user_id = %s AND account_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (current_user.id, account.id))
        
        recent_trades = []
        for row in cursor.fetchall():
            trade_dict = dict(zip([desc[0] for desc in cursor.description], row))
            
            # Normalize action field
            if 'action' in trade_dict and trade_dict['action']:
                trade_dict['action'] = trade_dict['action'].upper()
                if trade_dict['action'] not in ['BUY', 'SELL']:
                    trade_dict['action'] = 'BUY'  # Default to BUY
            
            # Convert Decimal to float - including quantity which might be stored as text
            for field in ['quantity', 'entry_price', 'current_price', 'floating_pnl', 'pnl']:
                if trade_dict.get(field) is not None:
                    try:
                        trade_dict[field] = float(trade_dict[field])
                    except (ValueError, TypeError):
                        trade_dict[field] = 0.0 if field == 'quantity' else None
            
            recent_trades.append(trade_dict)
        
        # Combine results
        analytics = dict(zip([desc[0] for desc in cursor.description], signal_stats))
        trade_dict = dict(zip(['total_trades', 'open_trades', 'pending_trades', 'winning_trades', 
                               'losing_trades', 'total_pnl', 'avg_pnl', 'avg_trade_duration_hours', 
                               'total_floating_pnl'], 
                               trade_stats))
        analytics.update(trade_dict)
        
        # Convert Decimal to float for JSON serialization
        analytics['total_pnl'] = float(analytics['total_pnl'])
        analytics['avg_pnl'] = float(analytics['avg_pnl'])
        analytics['total_floating_pnl'] = float(analytics['total_floating_pnl'])
        
        # Use account-level win rate and realized P&L if available
        if account_metrics:
            analytics['realized_pnl'] = float(account_metrics[0]) if account_metrics[0] else 0
            analytics['realized_pnl_updated_at'] = account_metrics[1].isoformat() if account_metrics[1] else None
            analytics['win_rate'] = float(account_metrics[2]) if account_metrics[2] else 0
        else:
            # Fallback to calculated win rate if account metrics not available
            closed_trades = analytics['winning_trades'] + analytics['losing_trades']
            if closed_trades > 0:
                analytics['win_rate'] = (analytics['winning_trades'] / closed_trades) * 100
            else:
                analytics['win_rate'] = 0
            analytics['realized_pnl'] = analytics['total_pnl']
            analytics['realized_pnl_updated_at'] = None
        
        # Add account info
        analytics['active_account'] = account.name
        analytics['account_type'] = account.account_type
        
        # Add recent trades
        analytics['recent_trades'] = recent_trades
        
        return analytics
    finally:
        conn.close()

# Auth endpoints
@app.post("/api/auth/login")
async def login(request: Request):
    """Login endpoint"""
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            raise HTTPException(status_code=422, detail="Username and password required")
        
        user = authenticate_user(username, password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/auth/register")
async def register_user(user_data: UserCreate):
    """Register a new user"""
    return await register(user_data.username, user_data.email, user_data.password)

# Account management endpoints
@app.get("/api/accounts", response_model=List[Account])
async def get_accounts(current_user: User = Depends(get_current_user)):
    """Get all accounts for the current user"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM accounts 
            WHERE user_id = %s 
            ORDER BY is_default DESC, created_at DESC
        """, (current_user.id,))
        
        accounts = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            accounts.append(Account(**dict(zip(columns, row))))
        
        return accounts
    finally:
        conn.close()

@app.post("/api/accounts", response_model=Account)
async def create_account(
    account: AccountCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new trading account"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if this is the first account (make it default)
        cursor.execute("SELECT COUNT(*) FROM accounts WHERE user_id = %s", (current_user.id,))
        is_first = cursor.fetchone()[0] == 0
        
        # If this account is set as default, unset other defaults
        if account.is_default or is_first:
            cursor.execute(
                "UPDATE accounts SET is_default = FALSE WHERE user_id = %s",
                (current_user.id,)
            )
        
        # Create the account
        cursor.execute("""
            INSERT INTO accounts (
                user_id, name, account_type, broker, 
                api_key, api_secret, base_url, 
                is_active, is_default
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            current_user.id, account.name, account.account_type, account.broker,
            account.api_key, account.api_secret, account.base_url,
            account.is_active, account.is_default or is_first
        ))
        
        new_account = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        
        conn.commit()
        return Account(**dict(zip(columns, new_account)))
    finally:
        conn.close()

@app.put("/api/accounts/{account_id}", response_model=Account)
async def update_account(
    account_id: int,
    account_update: AccountUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a trading account"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute(
            "SELECT * FROM accounts WHERE id = %s AND user_id = %s",
            (account_id, current_user.id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Build update query
        update_fields = []
        update_values = []
        
        if account_update.name is not None:
            update_fields.append("name = %s")
            update_values.append(account_update.name)
        if account_update.api_key is not None:
            update_fields.append("api_key = %s")
            update_values.append(account_update.api_key)
        if account_update.api_secret is not None:
            update_fields.append("api_secret = %s")
            update_values.append(account_update.api_secret)
        if account_update.base_url is not None:
            update_fields.append("base_url = %s")
            update_values.append(account_update.base_url)
        if account_update.is_active is not None:
            update_fields.append("is_active = %s")
            update_values.append(account_update.is_active)
        
        # Handle default flag
        if account_update.is_default is not None:
            if account_update.is_default:
                # Unset other defaults
                cursor.execute(
                    "UPDATE accounts SET is_default = FALSE WHERE user_id = %s AND id != %s",
                    (current_user.id, account_id)
                )
            update_fields.append("is_default = %s")
            update_values.append(account_update.is_default)
        
        if update_fields:
            update_values.append(account_id)
            cursor.execute(f"""
                UPDATE accounts 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING *
            """, update_values)
            
            updated_account = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            conn.commit()
            
            return Account(**dict(zip(columns, updated_account)))
        else:
            raise HTTPException(status_code=400, detail="No fields to update")
            
    finally:
        conn.close()

@app.delete("/api/accounts/{account_id}")
async def delete_account(
    account_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a trading account"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify ownership and not the last account
        cursor.execute(
            "SELECT COUNT(*) FROM accounts WHERE user_id = %s",
            (current_user.id,)
        )
        if cursor.fetchone()[0] <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete your last account")
        
        # Delete the account
        cursor.execute(
            "DELETE FROM accounts WHERE id = %s AND user_id = %s RETURNING id",
            (account_id, current_user.id)
        )
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Account not found")
        
        conn.commit()
        return {"message": "Account deleted successfully"}
        
    finally:
        conn.close()

@app.post("/api/accounts/{account_id}/activate")
async def activate_account(
    account_id: int,
    current_user: User = Depends(get_current_user)
):
    """Set an account as the active account"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify account exists and belongs to user
        cursor.execute(
            "SELECT * FROM accounts WHERE id = %s AND user_id = %s AND is_active = TRUE",
            (account_id, current_user.id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Account not found or inactive")
        
        # Update or create user session
        cursor.execute("""
            INSERT INTO user_sessions (user_id, active_account_id, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET active_account_id = %s, updated_at = %s
        """, (
            current_user.id, account_id, datetime.utcnow(),
            account_id, datetime.utcnow()
        ))
        
        conn.commit()
        return {"message": "Account activated successfully", "account_id": account_id}
        
    finally:
        conn.close()

@app.get("/api/accounts/active")
async def get_active_account_endpoint(current_user: User = Depends(get_current_user)):
    """Get the currently active account"""
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=404, detail="No active account found")
    return account

# Signal Source Management endpoints
@app.get("/api/sources", response_model=List[SignalSource])
async def get_signal_sources(current_user: User = Depends(get_current_user)):
    """Get all signal sources for the current user"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get sources with their account mappings
        cursor.execute("""
            SELECT ss.*,
                   COALESCE(
                       json_agg(
                           json_build_object(
                               'account_id', sa.account_id,
                               'auto_approve', sa.auto_approve,
                               'account_name', a.name,
                               'account_type', a.account_type
                           ) ORDER BY a.name
                       ) FILTER (WHERE sa.account_id IS NOT NULL), 
                       '[]'::json
                   ) as accounts
            FROM signal_sources ss
            LEFT JOIN source_accounts sa ON ss.id = sa.source_id
            LEFT JOIN accounts a ON sa.account_id = a.id AND a.user_id = %s
            WHERE ss.user_id = %s
            GROUP BY ss.id
            ORDER BY ss.created_at DESC
        """, (current_user.id, current_user.id))
        
        sources = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            source_dict = dict(zip(columns, row))
            sources.append(SignalSource(**source_dict))
        
        return sources
    finally:
        conn.close()

@app.post("/api/sources", response_model=SignalSource)
async def create_signal_source(
    source: SignalSourceCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new signal source configuration"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Generate unique webhook token
        webhook_token = secrets.token_urlsafe(32)
        
        # Create the source
        cursor.execute("""
            INSERT INTO signal_sources (
                user_id, source_type, source_identifier, 
                name, description, is_active, filter_config, webhook_token
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            current_user.id, source.source_type, source.source_identifier,
            source.name, source.description, source.is_active,
            json.dumps(source.filter_config), webhook_token
        ))
        
        new_source = cursor.fetchone()
        source_id = new_source[0]
        
        # Add account mappings
        for account_id in source.account_ids:
            auto_approve = source.auto_approve.get(str(account_id), False)
            cursor.execute("""
                INSERT INTO source_accounts (source_id, account_id, auto_approve)
                VALUES (%s, %s, %s)
            """, (source_id, account_id, auto_approve))
        
        # Fetch the complete source with accounts
        cursor.execute("""
            SELECT ss.*,
                   COALESCE(
                       json_agg(
                           json_build_object(
                               'account_id', sa.account_id,
                               'auto_approve', sa.auto_approve,
                               'account_name', a.name,
                               'account_type', a.account_type
                           )
                       ) FILTER (WHERE sa.account_id IS NOT NULL), 
                       '[]'::json
                   ) as accounts
            FROM signal_sources ss
            LEFT JOIN source_accounts sa ON ss.id = sa.source_id
            LEFT JOIN accounts a ON sa.account_id = a.id
            WHERE ss.id = %s
            GROUP BY ss.id
        """, (source_id,))
        
        source_data = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        
        conn.commit()
        return SignalSource(**dict(zip(columns, source_data)))
        
    finally:
        conn.close()

@app.put("/api/sources/{source_id}", response_model=SignalSource)
async def update_signal_source(
    source_id: int,
    source_update: SignalSourceUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a signal source configuration"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify ownership
        cursor.execute(
            "SELECT id FROM signal_sources WHERE id = %s AND user_id = %s",
            (source_id, current_user.id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Source not found")
        
        # Update source fields
        update_fields = []
        update_values = []
        
        if source_update.name is not None:
            update_fields.append("name = %s")
            update_values.append(source_update.name)
        if source_update.description is not None:
            update_fields.append("description = %s")
            update_values.append(source_update.description)
        if source_update.is_active is not None:
            update_fields.append("is_active = %s")
            update_values.append(source_update.is_active)
        if source_update.filter_config is not None:
            update_fields.append("filter_config = %s")
            update_values.append(json.dumps(source_update.filter_config))
        
        if update_fields:
            update_fields.append("updated_at = %s")
            update_values.append(datetime.utcnow())
            update_values.append(source_id)
            
            cursor.execute(f"""
                UPDATE signal_sources 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """, update_values)
        
        # Update account mappings if provided
        if source_update.account_ids is not None:
            # Remove existing mappings
            cursor.execute("DELETE FROM source_accounts WHERE source_id = %s", (source_id,))
            
            # Add new mappings
            for account_id in source_update.account_ids:
                auto_approve = False
                if source_update.auto_approve:
                    auto_approve = source_update.auto_approve.get(str(account_id), False)
                    
                cursor.execute("""
                    INSERT INTO source_accounts (source_id, account_id, auto_approve)
                    VALUES (%s, %s, %s)
                """, (source_id, account_id, auto_approve))
        
        # Fetch updated source
        cursor.execute("""
            SELECT ss.*,
                   COALESCE(
                       json_agg(
                           json_build_object(
                               'account_id', sa.account_id,
                               'auto_approve', sa.auto_approve,
                               'account_name', a.name,
                               'account_type', a.account_type
                           )
                       ) FILTER (WHERE sa.account_id IS NOT NULL), 
                       '[]'::json
                   ) as accounts
            FROM signal_sources ss
            LEFT JOIN source_accounts sa ON ss.id = sa.source_id
            LEFT JOIN accounts a ON sa.account_id = a.id
            WHERE ss.id = %s
            GROUP BY ss.id
        """, (source_id,))
        
        source_data = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        
        conn.commit()
        return SignalSource(**dict(zip(columns, source_data)))
        
    finally:
        conn.close()

@app.delete("/api/sources/{source_id}")
async def delete_signal_source(
    source_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a signal source"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Delete source (cascade will handle mappings)
        cursor.execute(
            "DELETE FROM signal_sources WHERE id = %s AND user_id = %s RETURNING id",
            (source_id, current_user.id)
        )
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Source not found")
        
        conn.commit()
        return {"message": "Source deleted successfully"}
        
    finally:
        conn.close()

@app.get("/api/sources/available-instances")
async def get_available_instances(current_user: User = Depends(get_current_user)):
    """Get available WHAPI instance IDs from webhook logs"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get unique instance IDs from recent webhook logs
        cursor.execute("""
            SELECT DISTINCT instance_id, COUNT(*) as message_count
            FROM webhook_logs
            WHERE instance_id IS NOT NULL AND instance_id != ''
            AND created_at > NOW() - INTERVAL '30 days'
            GROUP BY instance_id
            ORDER BY message_count DESC
            LIMIT 10
        """)
        
        instances = []
        for row in cursor.fetchall():
            instances.append({
                "instance_id": row[0],
                "message_count": row[1]
            })
        
        return {"instances": instances}
        
    finally:
        conn.close()

@app.post("/api/trades/calculate-pnl-from-alpaca")
async def calculate_pnl_from_alpaca(current_user: User = Depends(get_current_user)):
    """Calculate P&L directly from Alpaca order history using FIFO matching and save to account."""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get all filled orders from Alpaca
        all_orders = await broker_client.get_orders(status='all', limit=500)
        
        # Filter only filled orders and organize by symbol
        orders_by_symbol = {}
        for order in all_orders:
            if order['status'] == 'filled':
                symbol = order['symbol']
                if symbol not in orders_by_symbol:
                    orders_by_symbol[symbol] = {'buys': [], 'sells': []}
                
                order_data = {
                    'id': order['id'],
                    'qty': float(order['filled_qty']),
                    'price': float(order['filled_avg_price']),
                    'time': order['filled_at'],
                    'side': order['side'].upper()
                }
                
                if order['side'].upper() == 'BUY':
                    orders_by_symbol[symbol]['buys'].append(order_data)
                else:
                    orders_by_symbol[symbol]['sells'].append(order_data)
        
        # Calculate P&L for each symbol using FIFO
        total_realized_pnl = 0
        symbol_pnls = {}
        winning_trades = 0
        losing_trades = 0
        total_closed_trades = 0
        
        for symbol, orders in orders_by_symbol.items():
            # Sort by time (oldest first for FIFO)
            buys = sorted(orders['buys'], key=lambda x: x['time'])
            sells = sorted(orders['sells'], key=lambda x: x['time'])
            
            # FIFO matching
            buy_queue = []
            realized_pnl = 0
            
            for buy in buys:
                buy_queue.append({
                    'qty': buy['qty'],
                    'price': buy['price'],
                    'remaining': buy['qty']
                })
            
            for sell in sells:
                sell_qty = sell['qty']
                sell_price = sell['price']
                sell_id = sell['id']
                sell_pnl = 0
                matched = False
                
                # Match against buy queue (FIFO)
                while sell_qty > 0 and buy_queue:
                    buy_order = buy_queue[0]
                    match_qty = min(buy_order['remaining'], sell_qty)
                    pnl = (sell_price - buy_order['price']) * match_qty
                    sell_pnl += pnl
                    realized_pnl += pnl
                    buy_order['remaining'] -= match_qty
                    sell_qty -= match_qty
                    matched = True
                    # Track win/loss per match
                    total_closed_trades += 1
                    if pnl > 0:
                        winning_trades += 1
                    elif pnl < 0:
                        losing_trades += 1
                    if buy_order['remaining'] == 0:
                        buy_queue.pop(0)
                
                # Update database with calculated P&L for this SELL trade
                if matched:
                    cursor.execute("""
                        UPDATE trades 
                        SET pnl = %s
                        WHERE broker_order_id = %s AND action = 'SELL'
                    """, (
                        sell_pnl,
                        sell_id
                    ))
            
            symbol_pnls[symbol] = realized_pnl
            total_realized_pnl += realized_pnl
        
        conn.commit()
        
        # Calculate win rate
        win_rate = 0
        if total_closed_trades > 0:
            win_rate = (winning_trades / total_closed_trades) * 100
        
        # Save realized P&L and win rate to the account
        cursor.execute("""
            UPDATE accounts
            SET realized_pnl = %s,
                realized_pnl_updated_at = NOW(),
                win_rate = %s
            WHERE id = %s
        """, (total_realized_pnl, win_rate, account.id))
        conn.commit()
        
        return {
            "message": "P&L calculated from Alpaca data and saved to account",
            "total_realized_pnl": total_realized_pnl,
            "symbol_pnls": symbol_pnls,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "total_closed_trades": total_closed_trades,
            "win_rate": win_rate
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error calculating P&L from Alpaca: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Health check for deployment
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/trades/sync")
async def sync_trades_with_broker(current_user: User = Depends(get_current_user)):
    """Sync trade statuses with broker (Alpaca)"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        all_orders = await broker_client.get_orders(status='all', limit=500)
        print(f"Fetched {len(all_orders)} orders from Alpaca")  # <-- LOG TO BACKEND CONSOLE
        order_ids = [str(order['id']) for order in all_orders]
        imported_count = 0
        updated_count = 0
        
        # Fetch all open positions from Alpaca
        positions = await broker_client.get_positions()
        # Build a symbol -> position map for quick lookup
        position_map = {pos['symbol']: pos for pos in positions}
        
        for order in all_orders:
            broker_order_id = str(order['id'])
            # Check if we have this order
            cursor.execute("""
                SELECT id, entry_price, quantity, action, status, symbol FROM trades 
                WHERE broker_order_id = %s
            """, (broker_order_id,))
            existing_trade = cursor.fetchone()
            # Map Alpaca status to our status
            alpaca_status = order['status']
            our_status = 'pending'
            if alpaca_status == 'filled':
                # SELL orders should be marked as closed when filled
                if order['side'].upper() == 'SELL':
                    our_status = 'closed'
                else:
                    our_status = 'open'
            elif alpaca_status in ['canceled', 'cancelled', 'expired', 'rejected']:
                our_status = 'cancelled'
            elif alpaca_status == 'partially_filled':
                our_status = 'open'
            # Determine closed_at and close_reason
            closed_at = order.get('canceled_at') or order.get('updated_at') if our_status == 'cancelled' else None
            close_reason = None
            if our_status == 'cancelled':
                if alpaca_status in ['canceled', 'cancelled']:
                    close_reason = 'Order cancelled'
                elif alpaca_status == 'expired':
                    close_reason = 'Order expired'
                elif alpaca_status == 'rejected':
                    close_reason = 'Order rejected by broker'
            pnl = None
            floating_pnl = None
            if existing_trade:
                trade_id, entry_price, quantity, action, db_status, symbol = existing_trade
                current_price = None
                
                # Special handling for SELL orders that are filled
                if action == 'SELL' and our_status == 'open' and alpaca_status == 'filled':
                    # Check if this is a position close
                    cursor.execute("""
                        SELECT data FROM trade_notifications 
                        WHERE trade_id = %s
                    """, (trade_id,))
                    notifications = cursor.fetchall()
                    
                    for notification in notifications:
                        if notification[0]:
                            # Parse the JSON data
                            notif_data = notification[0] if isinstance(notification[0], dict) else json.loads(notification[0])
                            
                            # Check if this is a position close notification
                            if notif_data.get('notification_type') == 'position_close_pending':
                                # This is a position close, calculate P&L
                                positions_to_close = notif_data.get('positions_to_close', [])
                                sell_price = float(order.get('filled_avg_price', 0))
                                
                                total_pnl = 0
                                for pos in positions_to_close:
                                    pos_entry_price = pos['entry_price']
                                    pos_close_quantity = pos['close_quantity']
                                    # Calculate P&L for this portion
                                    pos_pnl = (sell_price - pos_entry_price) * pos_close_quantity
                                    total_pnl += pos_pnl
                                    
                                    # Update the original BUY trade
                                    if pos['remaining_quantity'] > 0:
                                        # Partial close - update quantity
                                        cursor.execute("""
                                            UPDATE trades 
                                            SET quantity = %s
                                            WHERE id = %s
                                        """, (pos['remaining_quantity'], pos['id']))
                                    else:
                                        # Full close - mark as closed
                                        cursor.execute("""
                                            UPDATE trades 
                                            SET status = 'closed',
                                                exit_price = %s,
                                                pnl = %s,
                                                closed_at = %s,
                                                close_reason = 'Position closed'
                                            WHERE id = %s
                                        """, (sell_price, pos_pnl, order.get('filled_at'), pos['id']))
                                
                                # Update the SELL trade with total P&L
                                pnl = total_pnl
                                our_status = 'closed'  # Mark SELL trades as closed when filled
                                
                                # Update the notification to mark it as processed
                                notif_data['notification_type'] = 'position_close_completed'
                                cursor.execute("""
                                    UPDATE trade_notifications 
                                    SET data = %s
                                    WHERE trade_id = %s AND id = (
                                        SELECT id FROM trade_notifications 
                                        WHERE trade_id = %s 
                                        ORDER BY created_at DESC 
                                        LIMIT 1
                                    )
                                """, (json.dumps(notif_data), trade_id, trade_id))
                                
                                break  # We found and processed the position close
                
                # Always try to get the latest price for open trades
                if our_status == 'open' and action == 'BUY':
                    if symbol in position_map:
                        current_price = float(position_map[symbol].get('current_price', 0))
                    else:
                        # Fallback: get market data if no position (e.g. just opened)
                        market_data = await broker_client.get_market_data(symbol)
                        current_price = float(market_data.get('last', 0))
                    # Calculate floating P&L for open trades
                    if entry_price is not None and quantity is not None:
                        try:
                            floating_pnl = (current_price - float(entry_price)) * float(quantity) if action == 'BUY' else (float(entry_price) - current_price) * float(quantity)
                        except Exception:
                            floating_pnl = 0
                else:
                    current_price = float(order.get('filled_avg_price') or order.get('limit_price') or 0)
                # Update all relevant fields
                exit_price = None
                if our_status == 'closed':
                    exit_price = float(order.get('filled_avg_price') or order.get('limit_price') or 0)
                    current_price = None  # Don't set current_price for closed trades
                
                cursor.execute("""
                    UPDATE trades 
                    SET status = %s,
                        symbol = %s,
                        action = %s,
                        quantity = %s,
                        entry_price = %s,
                        exit_price = %s,
                        broker_fill_price = %s,
                        opened_at = %s,
                        current_price = %s,
                        pnl = %s,
                        floating_pnl = %s,
                        closed_at = %s,
                        close_reason = %s
                    WHERE broker_order_id = %s
                """, (
                    our_status,
                    order['symbol'],
                    order['side'].upper(),
                    float(order.get('filled_qty') or order.get('qty', 0)),
                    float(order.get('filled_avg_price') or order.get('limit_price') or 0),
                    exit_price,
                    float(order.get('filled_avg_price') or 0),
                    order.get('filled_at') or order.get('updated_at'),
                    current_price,
                    pnl,
                    floating_pnl,
                    closed_at if our_status != 'closed' else order.get('filled_at'),
                    close_reason if our_status != 'closed' else 'Position closed',
                    broker_order_id
                ))
                updated_count += 1
            else:
                # Insert new trade (same as before)
                current_price = float(order.get('filled_avg_price') or order.get('limit_price') or 0)
                cursor.execute("""
                    INSERT INTO trades (
                        user_id, account_id, symbol, action, quantity,
                        entry_price, broker_fill_price, status,
                        broker_order_id, created_at, opened_at,
                        current_price, pnl, floating_pnl, closed_at, close_reason
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    current_user.id,
                    account.id,
                    order['symbol'],
                    order['side'].upper(),
                    float(order.get('filled_qty') or order.get('qty', 0)),
                    float(order.get('filled_avg_price') or order.get('limit_price') or 0),
                    float(order.get('filled_avg_price') or 0),
                    our_status,
                    broker_order_id,
                    order.get('created_at'),
                    order.get('filled_at') if our_status == 'open' else None,
                    current_price,
                    pnl,
                    floating_pnl,
                    closed_at,
                    close_reason
                ))
                imported_count += 1
        
        conn.commit()
        
        return {
            "message": "Sync completed",
            "total_orders": len(all_orders),
            "imported": imported_count,
            "updated": updated_count,
            "alpaca_order_ids": order_ids  # <-- RETURN TO FRONTEND
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error syncing trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/trades/link")
async def link_trades(
    trade_ids: List[int],
    current_user: User = Depends(get_current_user)
):
    """Link multiple trades together with a common group ID"""
    import uuid
    
    if len(trade_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 trades are required for linking")
    
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify all trades belong to current user and account
        cursor.execute("""
            SELECT id, symbol, action, quantity, status 
            FROM trades 
            WHERE id = ANY(%s) AND user_id = %s AND account_id = %s
        """, (trade_ids, current_user.id, account.id))
        
        trades = cursor.fetchall()
        if len(trades) != len(trade_ids):
            raise HTTPException(status_code=404, detail="Some trades not found or don't belong to current user")
        
        # Generate a new link group ID
        link_group_id = str(uuid.uuid4())
        
        # Link all trades
        cursor.execute("""
            UPDATE trades 
            SET link_group_id = %s 
            WHERE id = ANY(%s)
        """, (link_group_id, trade_ids))
        
        conn.commit()
        
        return {
            "message": f"Successfully linked {len(trade_ids)} trades",
            "link_group_id": link_group_id,
            "trades": [
                {
                    "id": trade[0],
                    "symbol": trade[1], 
                    "action": trade[2],
                    "quantity": float(trade[3]),
                    "status": trade[4]
                } 
                for trade in trades
            ]
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/trades/unlink")
async def unlink_trades(
    trade_ids: List[int],
    current_user: User = Depends(get_current_user)
):
    """Unlink trades by removing their link group ID"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify trades belong to current user and account
        cursor.execute("""
            SELECT COUNT(*) FROM trades 
            WHERE id = ANY(%s) AND user_id = %s AND account_id = %s
        """, (trade_ids, current_user.id, account.id))
        
        if cursor.fetchone()[0] != len(trade_ids):
            raise HTTPException(status_code=404, detail="Some trades not found or don't belong to current user")
        
        # Unlink trades
        cursor.execute("""
            UPDATE trades 
            SET link_group_id = NULL 
            WHERE id = ANY(%s)
        """, (trade_ids,))
        
        conn.commit()
        
        return {"message": f"Successfully unlinked {len(trade_ids)} trades"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/trades/import-positions")
async def import_positions_from_broker(current_user: User = Depends(get_current_user)):
    """Import current positions from broker that aren't tracked in the database"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get current positions from Alpaca
        positions = await broker_client.get_positions()
        imported_count = 0
        
        for position in positions:
            # Check if we already have this position tracked
            cursor.execute("""
                SELECT COUNT(*) FROM trades 
                WHERE symbol = %s 
                AND user_id = %s 
                AND account_id = %s 
                AND status = 'open'
                AND quantity = %s
            """, (
                position['symbol'],
                current_user.id,
                account.id,
                position['qty']
            ))
            
            exists = cursor.fetchone()[0] > 0
            
            if not exists:
                # Import this position as a new trade
                cursor.execute("""
                    INSERT INTO trades (
                        user_id, account_id, symbol, action, quantity,
                        entry_price, broker_fill_price, current_price,
                        status, opened_at, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'open', %s, %s)
                    RETURNING id
                """, (
                    current_user.id,
                    account.id,
                    position['symbol'],
                    position['side'].upper(),
                    position['qty'],
                    position['avg_entry_price'],
                    position['avg_entry_price'],
                    position['current_price'],
                    datetime.utcnow(),  # We don't know actual open time
                    datetime.utcnow()
                ))
                
                imported_count += 1
        
        conn.commit()
        
        return {
            "message": "Import completed",
            "positions_found": len(positions),
            "positions_imported": imported_count
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error importing positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time trade updates"""
    # Validate token and get user
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            await websocket.close(code=1008, reason="Invalid token")
            return
            
        # Get user from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
            
        user_id = user[0]
        
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    # Connect the WebSocket
    await manager.connect(websocket, user_id)
    
    try:
        # Keep connection alive
        while True:
            # Wait for any message from client (ping/pong)
            data = await websocket.receive_text()
            
            # Handle ping
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Helper function to notify users of trade updates
async def notify_trade_update(user_id: int, trade_data: dict):
    """Send real-time trade update to user via WebSocket"""
    await manager.broadcast_to_user({
        "type": "trade_update",
        "data": trade_data,
        "timestamp": datetime.utcnow().isoformat()
    }, user_id)

@app.get("/api/notifications/trades")
async def get_trade_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Get recent trade notifications for the current user"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM trade_notifications 
            WHERE user_id = %s
        """
        params = [current_user.id]
        
        if unread_only:
            query += " AND read = FALSE"
            
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        
        notifications = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            notification = dict(zip(columns, row))
            # Parse JSON data field
            if notification.get('data'):
                notification['data'] = json.loads(notification['data']) if isinstance(notification['data'], str) else notification['data']
            notifications.append(notification)
        
        return notifications
        
    finally:
        conn.close()

@app.post("/api/notifications/trades/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE trade_notifications 
            SET read = TRUE 
            WHERE id = %s AND user_id = %s
        """, (notification_id, current_user.id))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
        
    finally:
        conn.close()

@app.get("/api/market-data/{symbol}")
async def get_market_data(symbol: str, current_user: User = Depends(get_current_user)):
    """Get current market data for a symbol from Alpaca"""
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    data = await broker_client.get_market_data(symbol)
    return data

@app.delete("/api/signals/{signal_id}")
async def delete_signal(signal_id: int, current_user: User = Depends(get_current_user)):
    """Delete/cancel a signal if it is pending or approved and belongs to the user/account."""
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Only allow deleting signals that are pending or approved and belong to the user/account
        cursor.execute("""
            DELETE FROM signals
            WHERE id = %s AND (status = 'pending' OR status = 'approved') AND (user_id = %s OR account_id = %s)
            RETURNING id
        """, (signal_id, current_user.id, account.id))
        deleted = cursor.fetchone()
        if not deleted:
            raise HTTPException(status_code=404, detail="Signal not found or cannot be deleted")
        conn.commit()
        return {"message": "Signal deleted"}
    finally:
        conn.close()

@app.get("/api/positions")
async def get_positions(current_user: User = Depends(get_current_user)):
    """Get aggregated positions from Alpaca"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    
    try:
        # Get positions from Alpaca
        positions = await broker_client.get_positions()
        
        # Format positions for frontend
        formatted_positions = []
        for pos in positions:
            # Calculate P&L
            qty = float(pos.get('qty', 0))
            avg_entry_price = float(pos.get('avg_entry_price', 0))
            current_price = float(pos.get('current_price', 0))
            market_value = float(pos.get('market_value', 0))
            cost_basis = float(pos.get('cost_basis', 0))
            
            # Calculate unrealized P&L
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            # Calculate today's P&L if available
            change_today = float(pos.get('change_today', 0))
            today_pnl = change_today * qty
            today_pnl_pct = (change_today / (current_price - change_today) * 100) if (current_price - change_today) > 0 else 0
            
            formatted_positions.append({
                'symbol': pos.get('symbol'),
                'side': pos.get('side', 'long').upper(),
                'quantity': qty,
                'avg_entry_price': avg_entry_price,
                'current_price': current_price,
                'market_value': market_value,
                'cost_basis': cost_basis,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'today_pnl': today_pnl,
                'today_pnl_pct': today_pnl_pct,
                'asset_class': pos.get('asset_class', 'us_equity'),
                'exchange': pos.get('exchange', 'NASDAQ')
            })
        
        return formatted_positions
        
    except Exception as e:
        print(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions/sync")
async def sync_positions(current_user: User = Depends(get_current_user)):
    """Sync positions from Alpaca - similar to trades sync but for positions view"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    
    try:
        # Get positions from Alpaca
        positions = await broker_client.get_positions()
        
        # Update current prices for open trades in database
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            for pos in positions:
                symbol = pos.get('symbol')
                current_price = float(pos.get('current_price', 0))
                
                # Update all open trades for this symbol with current price
                cursor.execute("""
                    UPDATE trades 
                    SET current_price = %s,
                        floating_pnl = CASE 
                            WHEN action = 'BUY' THEN ((%s - entry_price) * quantity)
                            ELSE ((entry_price - %s) * quantity)
                        END
                    WHERE symbol = %s 
                    AND user_id = %s 
                    AND account_id = %s 
                    AND status = 'open'
                """, (
                    current_price, current_price, current_price,
                    symbol, current_user.id, account.id
                ))
            
            conn.commit()
            
            return {
                "message": "Positions synced successfully",
                "positions_count": len(positions)
            }
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error syncing positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/trades/recalculate-pnl")
async def recalculate_pnl(current_user: User = Depends(get_current_user)):
    """Recalculate P&L for all trades based on position close notifications"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Find all SELL trades that might be position closes
        cursor.execute("""
            SELECT t.id, t.symbol, t.quantity, t.broker_fill_price, t.broker_order_id
            FROM trades t
            WHERE t.user_id = %s 
            AND t.account_id = %s 
            AND t.action = 'SELL'
            AND t.status = 'closed'
        """, (current_user.id, account.id))
        
        sell_trades = cursor.fetchall()
        recalculated_count = 0
        
        for sell_trade in sell_trades:
            trade_id, symbol, sell_quantity, sell_price, broker_order_id = sell_trade
            
            # Check if we have position close notification
            cursor.execute("""
                SELECT data FROM trade_notifications 
                WHERE trade_id = %s
            """, (trade_id,))
            
            notifications = cursor.fetchall()
            
            for notification in notifications:
                if notification[0]:
                    notif_data = notification[0] if isinstance(notification[0], dict) else json.loads(notification[0])
                    
                    if notif_data.get('notification_type') in ['position_close_pending', 'position_close_completed']:
                        positions_to_close = notif_data.get('positions_to_close', [])
                        
                        if positions_to_close:
                            total_pnl = 0
                            for pos in positions_to_close:
                                pos_entry_price = float(pos['entry_price'])
                                pos_close_quantity = float(pos['close_quantity'])
                                # Calculate P&L for this portion
                                pos_pnl = (float(sell_price) - pos_entry_price) * pos_close_quantity
                                total_pnl += pos_pnl
                            
                            # Update the SELL trade with P&L
                            cursor.execute("""
                                UPDATE trades 
                                SET pnl = %s,
                                    exit_price = %s
                                WHERE id = %s
                            """, (total_pnl, sell_price, trade_id))
                            
                            recalculated_count += 1
                            print(f"Recalculated P&L for trade {trade_id}: ${total_pnl:.2f}")
        
        conn.commit()
        
        return {
            "message": "P&L recalculation completed",
            "trades_updated": recalculated_count
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error recalculating P&L: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/sync-dashboard")
async def sync_dashboard(current_user: User = Depends(get_current_user)):
    """Consolidated sync endpoint that syncs trades and calculates P&L/win rate"""
    # Get active account
    account = await get_active_account(current_user)
    if not account:
        raise HTTPException(status_code=400, detail="No active trading account")
    
    # Get broker client
    broker_client = get_broker_client(account)
    if not broker_client:
        raise HTTPException(status_code=400, detail="Failed to initialize broker client")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Step 1: Sync trades with broker
        all_orders = await broker_client.get_orders(status='all', limit=500)
        print(f"Fetched {len(all_orders)} orders from Alpaca")
        
        imported_count = 0
        updated_count = 0
        
        # Fetch all open positions from Alpaca
        positions = await broker_client.get_positions()
        position_map = {pos['symbol']: pos for pos in positions}
        
        for order in all_orders:
            broker_order_id = str(order['id'])
            # Check if we have this order
            cursor.execute("""
                SELECT id, entry_price, quantity, action, status, symbol FROM trades 
                WHERE broker_order_id = %s
            """, (broker_order_id,))
            existing_trade = cursor.fetchone()
            
            # Map Alpaca status to our status
            alpaca_status = order['status']
            our_status = 'pending'
            if alpaca_status == 'filled':
                if order['side'].upper() == 'SELL':
                    our_status = 'closed'
                else:
                    our_status = 'open'
            elif alpaca_status in ['canceled', 'cancelled', 'expired', 'rejected']:
                our_status = 'cancelled'
            elif alpaca_status == 'partially_filled':
                our_status = 'open'
            
            closed_at = order.get('canceled_at') or order.get('updated_at') if our_status == 'cancelled' else None
            close_reason = None
            if our_status == 'cancelled':
                if alpaca_status in ['canceled', 'cancelled']:
                    close_reason = 'Order cancelled'
                elif alpaca_status == 'expired':
                    close_reason = 'Order expired'
                elif alpaca_status == 'rejected':
                    close_reason = 'Order rejected by broker'
            
            pnl = None
            floating_pnl = None
            
            if existing_trade:
                trade_id, entry_price, quantity, action, db_status, symbol = existing_trade
                current_price = None
                
                # Special handling for SELL orders that are filled
                if action == 'SELL' and our_status == 'open' and alpaca_status == 'filled':
                    # Check if this is a position close
                    cursor.execute("""
                        SELECT data FROM trade_notifications 
                        WHERE trade_id = %s
                    """, (trade_id,))
                    notifications = cursor.fetchall()
                    
                    for notification in notifications:
                        if notification[0]:
                            notif_data = notification[0] if isinstance(notification[0], dict) else json.loads(notification[0])
                            
                            if notif_data.get('notification_type') == 'position_close_pending':
                                positions_to_close = notif_data.get('positions_to_close', [])
                                sell_price = float(order.get('filled_avg_price', 0))
                                
                                total_pnl = 0
                                for pos in positions_to_close:
                                    pos_entry_price = pos['entry_price']
                                    pos_close_quantity = pos['close_quantity']
                                    pos_pnl = (sell_price - pos_entry_price) * pos_close_quantity
                                    total_pnl += pos_pnl
                                    
                                    if pos['remaining_quantity'] > 0:
                                        cursor.execute("""
                                            UPDATE trades 
                                            SET quantity = %s
                                            WHERE id = %s
                                        """, (pos['remaining_quantity'], pos['id']))
                                    else:
                                        cursor.execute("""
                                            UPDATE trades 
                                            SET status = 'closed',
                                                exit_price = %s,
                                                pnl = %s,
                                                closed_at = %s,
                                                close_reason = 'Position closed'
                                            WHERE id = %s
                                        """, (sell_price, pos_pnl, order.get('filled_at'), pos['id']))
                                
                                pnl = total_pnl
                                our_status = 'closed'
                                
                                notif_data['notification_type'] = 'position_close_completed'
                                cursor.execute("""
                                    UPDATE trade_notifications 
                                    SET data = %s
                                    WHERE trade_id = %s AND id = (
                                        SELECT id FROM trade_notifications 
                                        WHERE trade_id = %s 
                                        ORDER BY created_at DESC 
                                        LIMIT 1
                                    )
                                """, (json.dumps(notif_data), trade_id, trade_id))
                                
                                break
                
                # Always try to get the latest price for open trades
                if our_status == 'open' and action == 'BUY':
                    if symbol in position_map:
                        current_price = float(position_map[symbol].get('current_price', 0))
                    else:
                        market_data = await broker_client.get_market_data(symbol)
                        current_price = float(market_data.get('last', 0))
                    
                    if entry_price is not None and quantity is not None:
                        try:
                            floating_pnl = (current_price - float(entry_price)) * float(quantity) if action == 'BUY' else (float(entry_price) - current_price) * float(quantity)
                        except Exception:
                            floating_pnl = 0
                else:
                    current_price = float(order.get('filled_avg_price') or order.get('limit_price') or 0)
                
                # Update existing trade
                exit_price = None
                if our_status == 'closed':
                    exit_price = float(order.get('filled_avg_price') or order.get('limit_price') or 0)
                    current_price = None  # Don't set current_price for closed trades
                
                cursor.execute("""
                    UPDATE trades 
                    SET status = %s,
                        symbol = %s,
                        action = %s,
                        quantity = %s,
                        entry_price = %s,
                        exit_price = %s,
                        broker_fill_price = %s,
                        opened_at = %s,
                        current_price = %s,
                        pnl = %s,
                        floating_pnl = %s,
                        closed_at = %s,
                        close_reason = %s
                    WHERE broker_order_id = %s
                """, (
                    our_status,
                    order['symbol'],
                    order['side'].upper(),
                    float(order.get('filled_qty') or order.get('qty', 0)),
                    float(order.get('filled_avg_price') or order.get('limit_price') or 0),
                    exit_price,
                    float(order.get('filled_avg_price') or 0),
                    order.get('filled_at') or order.get('updated_at'),
                    current_price,
                    pnl,
                    floating_pnl,
                    closed_at if our_status != 'closed' else order.get('filled_at'),
                    close_reason if our_status != 'closed' else 'Position closed',
                    broker_order_id
                ))
                updated_count += 1
            else:
                # Insert new trade
                exit_price = None
                current_price = float(order.get('filled_avg_price') or order.get('limit_price') or 0)
                if our_status == 'closed':
                    exit_price = current_price
                    current_price = None  # Don't set current_price for closed trades
                
                cursor.execute("""
                    INSERT INTO trades (
                        user_id, account_id, symbol, action, quantity,
                        entry_price, exit_price, broker_fill_price, status,
                        broker_order_id, created_at, opened_at,
                        current_price, pnl, floating_pnl, closed_at, close_reason
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    current_user.id,
                    account.id,
                    order['symbol'],
                    order['side'].upper(),
                    float(order.get('filled_qty') or order.get('qty', 0)),
                    float(order.get('filled_avg_price') or order.get('limit_price') or 0),
                    exit_price,
                    float(order.get('filled_avg_price') or 0),
                    our_status,
                    broker_order_id,
                    order.get('created_at'),
                    order.get('filled_at') if our_status == 'open' else None,
                    current_price,
                    pnl,
                    floating_pnl,
                    closed_at,
                    close_reason
                ))
                imported_count += 1
        
        conn.commit()
        
        # Step 2: Calculate P&L and win rate from Alpaca data
        # Filter only filled orders and organize by symbol
        orders_by_symbol = {}
        for order in all_orders:
            if order['status'] == 'filled':
                symbol = order['symbol']
                if symbol not in orders_by_symbol:
                    orders_by_symbol[symbol] = {'buys': [], 'sells': []}
                
                order_data = {
                    'id': order['id'],
                    'qty': float(order['filled_qty']),
                    'price': float(order['filled_avg_price']),
                    'time': order['filled_at'],
                    'side': order['side'].upper()
                }
                
                if order['side'].upper() == 'BUY':
                    orders_by_symbol[symbol]['buys'].append(order_data)
                else:
                    orders_by_symbol[symbol]['sells'].append(order_data)
        
        # Calculate P&L for each symbol using FIFO
        total_realized_pnl = 0
        symbol_pnls = {}
        winning_trades = 0
        losing_trades = 0
        total_closed_trades = 0
        
        for symbol, orders in orders_by_symbol.items():
            # Sort by time (oldest first for FIFO)
            buys = sorted(orders['buys'], key=lambda x: x['time'])
            sells = sorted(orders['sells'], key=lambda x: x['time'])
            
            # FIFO matching
            buy_queue = []
            realized_pnl = 0
            
            for buy in buys:
                buy_queue.append({
                    'qty': buy['qty'],
                    'price': buy['price'],
                    'remaining': buy['qty']
                })
            
            for sell in sells:
                sell_qty = sell['qty']
                sell_price = sell['price']
                sell_id = sell['id']
                sell_pnl = 0
                matched = False
                
                # Match against buy queue (FIFO)
                while sell_qty > 0 and buy_queue:
                    buy_order = buy_queue[0]
                    match_qty = min(buy_order['remaining'], sell_qty)
                    pnl = (sell_price - buy_order['price']) * match_qty
                    sell_pnl += pnl
                    realized_pnl += pnl
                    buy_order['remaining'] -= match_qty
                    sell_qty -= match_qty
                    matched = True
                    # Track win/loss per match
                    total_closed_trades += 1
                    if pnl > 0:
                        winning_trades += 1
                    elif pnl < 0:
                        losing_trades += 1
                    if buy_order['remaining'] == 0:
                        buy_queue.pop(0)
                
                # Update database with calculated P&L for this SELL trade
                if matched:
                    cursor.execute("""
                        UPDATE trades 
                        SET pnl = %s
                        WHERE broker_order_id = %s AND action = 'SELL'
                    """, (
                        sell_pnl,
                        sell_id
                    ))
            
            symbol_pnls[symbol] = realized_pnl
            total_realized_pnl += realized_pnl
        
        # Calculate win rate
        win_rate = 0
        if total_closed_trades > 0:
            win_rate = (winning_trades / total_closed_trades) * 100
        
        # Save realized P&L and win rate to the account
        cursor.execute("""
            UPDATE accounts
            SET realized_pnl = %s,
                realized_pnl_updated_at = NOW(),
                win_rate = %s
            WHERE id = %s
        """, (total_realized_pnl, win_rate, account.id))
        conn.commit()
        
        # Get updated account data
        cursor.execute("""
            SELECT realized_pnl, realized_pnl_updated_at, win_rate
            FROM accounts
            WHERE id = %s
        """, (account.id,))
        account_data = cursor.fetchone()
        
        return {
            "message": "Dashboard synced successfully",
            "sync_results": {
                "total_orders": len(all_orders),
                "imported": imported_count,
                "updated": updated_count
            },
            "pnl_results": {
                "total_realized_pnl": float(account_data[0]) if account_data[0] else 0,
                "win_rate": float(account_data[2]) if account_data[2] else 0,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "total_closed_trades": total_closed_trades,
                "last_updated": account_data[1].isoformat() if account_data[1] else None
            },
            "symbol_pnls": symbol_pnls
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error syncing dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

async def process_trade_levels(trade_id: int, signal_dict: dict, filled_quantity: float, filled_price: float, cursor, custom_levels: dict = None):
    """
    Process and save take profit and stop loss levels after trade execution.
    
    Args:
        trade_id: The ID of the executed trade
        signal_dict: The original signal data with enhanced_data
        filled_quantity: The actual number of shares filled 
        filled_price: The actual fill price
        cursor: Database cursor
    """
    try:
        print(f"🔄 Processing trade levels for trade {trade_id} - {filled_quantity} shares at ${filled_price}")
        # Parse enhanced_data to get take profit levels and stop loss info
        enhanced_data = signal_dict.get('enhanced_data')
        if isinstance(enhanced_data, str):
            enhanced_data = json.loads(enhanced_data)
        elif not enhanced_data:
            enhanced_data = {}
        
        # Process take profit levels - use custom levels if provided, otherwise use enhanced_data
        custom_tp_levels = custom_levels.get('take_profit_levels', []) if custom_levels else []
        take_profit_levels = enhanced_data.get('take_profit_levels', [])
        
        # Use custom levels if provided
        if custom_tp_levels:
            print(f"Processing {len(custom_tp_levels)} custom take profit levels for trade {trade_id}")
            
            # Calculate shares for each take profit level using custom percentages
            total_shares_allocated = 0
            levels_data = []
            
            for i, level in enumerate(custom_tp_levels):
                tp_price = level.get('price', 0)
                percentage = level.get('percentage', 0)
                
                if tp_price <= 0 or percentage <= 0:
                    continue
                
                # Calculate shares for this level
                level_shares = floor(filled_quantity * (percentage / 100) * 10000) / 10000  # Round down to 4 decimals
                total_shares_allocated += level_shares
                
                levels_data.append({
                    'level_number': i + 1,
                    'price': float(tp_price),
                    'percentage': percentage,
                    'shares': level_shares
                })
                
            # Adjust last level if needed to ensure exact total
            if levels_data and abs(total_shares_allocated - filled_quantity) > 0.0001:
                adjustment = filled_quantity - total_shares_allocated
                levels_data[-1]['shares'] += adjustment
                print(f"Adjusted last level by {adjustment} shares to match total")
                
        elif take_profit_levels and isinstance(take_profit_levels, list):
            print(f"Processing {len(take_profit_levels)} default take profit levels for trade {trade_id}")
            
            # Calculate shares for each take profit level using equal distribution
            total_shares_allocated = 0
            levels_data = []
            
            for i, tp_price in enumerate(take_profit_levels):
                # Default percentage distribution - equal percentages except last level gets remainder
                if i < len(take_profit_levels) - 1:
                    percentage = 100 / len(take_profit_levels)  # Equal distribution
                else:
                    # Last level gets remaining percentage to ensure 100% total
                    percentage = 100 - sum(level['percentage'] for level in levels_data)
                
                # Calculate shares for this level (use floor to avoid over-allocation)
                if i < len(take_profit_levels) - 1:
                    level_shares = floor(filled_quantity * (percentage / 100) * 10000) / 10000  # Round down to 4 decimals
                else:
                    # Last level gets all remaining shares
                    level_shares = filled_quantity - total_shares_allocated
                
                total_shares_allocated += level_shares
                
                levels_data.append({
                    'level_number': i + 1,
                    'price': float(tp_price),
                    'percentage': percentage,
                    'shares': level_shares
                })
            
            # Verify total allocation equals filled quantity
            if abs(total_shares_allocated - filled_quantity) > 0.0001:
                print(f"Warning: Share allocation mismatch. Total: {total_shares_allocated}, Expected: {filled_quantity}")
                # Adjust last level to match exactly
                levels_data[-1]['shares'] = filled_quantity - sum(level['shares'] for level in levels_data[:-1])
        
        # Save take profit levels to database (works for both custom and default levels)
        if 'levels_data' in locals() and levels_data:
            # Check if take profit levels already exist
            cursor.execute("SELECT COUNT(*) FROM take_profit_levels WHERE trade_id = %s", (trade_id,))
            existing_tp_count = cursor.fetchone()[0]
            
            if existing_tp_count > 0:
                print(f"Take profit levels already exist for trade {trade_id}, skipping...")
            else:
                for level_data in levels_data:
                    try:
                        cursor.execute("""
                            INSERT INTO take_profit_levels (
                                trade_id, level_number, price, percentage, shares_quantity, status, created_at
                            )
                            VALUES (%s, %s, %s, %s, %s, 'pending', %s)
                        """, (
                            trade_id,
                            level_data['level_number'],
                            level_data['price'],
                            level_data['percentage'],
                            level_data['shares'],
                            datetime.utcnow()
                        ))
                        print(f"  - TP Level {level_data['level_number']}: ${level_data['price']} - {level_data['percentage']:.1f}% ({level_data['shares']} shares)")
                    except Exception as e:
                        print(f"    ✗ Error inserting TP Level {level_data['level_number']}: {e}")
        
        # Process stop loss level - use custom price if provided
        custom_sl_price = custom_levels.get('stop_loss_price') if custom_levels else None
        stop_loss_price = custom_sl_price or signal_dict.get('stop_loss') or enhanced_data.get('stop_loss')
        if stop_loss_price:
            try:
                stop_loss_price = float(stop_loss_price)
                if stop_loss_price > 0:
                    # Check if stop loss already exists
                    cursor.execute("SELECT COUNT(*) FROM stop_loss_levels WHERE trade_id = %s", (trade_id,))
                    existing_sl_count = cursor.fetchone()[0]
                    
                    if existing_sl_count > 0:
                        print(f"Stop loss level already exists for trade {trade_id}, skipping...")
                    else:
                        print(f"Processing stop loss at ${stop_loss_price} for trade {trade_id}")
                        
                        cursor.execute("""
                            INSERT INTO stop_loss_levels (
                                trade_id, price, status, created_at
                            )
                            VALUES (%s, %s, 'active', %s)
                        """, (
                            trade_id,
                            stop_loss_price,
                            datetime.utcnow()
                        ))
                        
                        print(f"  - Stop Loss: ${stop_loss_price} (all remaining shares)")
            except (ValueError, TypeError) as e:
                print(f"Error processing stop loss price '{stop_loss_price}': {e}")
            
    except Exception as e:
        print(f"Error processing trade levels for trade {trade_id}: {e}")
        import traceback
        traceback.print_exc()

@app.get("/api/trades/{trade_id}/levels")
async def get_trade_levels(trade_id: int, current_user: User = Depends(get_current_user)):
    """Get take profit and stop loss levels for a trade"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Verify the trade belongs to the user
        cursor.execute("""
            SELECT id FROM trades WHERE id = %s AND user_id = %s
        """, (trade_id, current_user.id))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Trade not found")
        
        # Get take profit levels
        cursor.execute("""
            SELECT * FROM take_profit_levels 
            WHERE trade_id = %s 
            ORDER BY level_number ASC
        """, (trade_id,))
        
        tp_levels = cursor.fetchall()
        take_profit_levels = []
        
        for level in tp_levels:
            take_profit_levels.append({
                "id": level[0],
                "level_number": level[2],
                "price": float(level[3]),
                "percentage": float(level[4]),
                "shares_quantity": float(level[5]),
                "status": level[6],
                "executed_at": level[7],
                "executed_price": float(level[8]) if level[8] else None,
                "broker_order_id": level[9],
                "created_at": level[10]
            })
        
        # Get stop loss level
        cursor.execute("""
            SELECT * FROM stop_loss_levels 
            WHERE trade_id = %s 
            ORDER BY created_at DESC
            LIMIT 1
        """, (trade_id,))
        
        sl_data = cursor.fetchone()
        stop_loss_level = None
        
        if sl_data:
            stop_loss_level = {
                "id": sl_data[0],
                "price": float(sl_data[2]),
                "status": sl_data[3],
                "executed_at": sl_data[4],
                "executed_price": float(sl_data[5]) if sl_data[5] else None,
                "executed_shares": float(sl_data[6]) if sl_data[6] else None,
                "broker_order_id": sl_data[7],
                "created_at": sl_data[8]
            }
        
        return {
            "trade_id": trade_id,
            "take_profit_levels": take_profit_levels,
            "stop_loss_level": stop_loss_level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting trade levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/monitoring/levels")
async def get_monitoring_levels(current_user: User = Depends(get_current_user)):
    """Get all active take profit and stop loss levels for monitoring"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get all pending take profit levels for the user
        cursor.execute("""
            SELECT 
                tp.id, tp.trade_id, tp.level_number, tp.price, tp.percentage, 
                tp.shares_quantity, tp.status, t.symbol, t.action
            FROM take_profit_levels tp
            JOIN trades t ON tp.trade_id = t.id
            WHERE t.user_id = %s AND tp.status = 'pending'
            ORDER BY t.symbol, tp.level_number
        """, (current_user.id,))
        
        tp_levels = cursor.fetchall()
        take_profit_monitoring = []
        
        for level in tp_levels:
            take_profit_monitoring.append({
                "id": level[0],
                "trade_id": level[1],
                "level_number": level[2],
                "price": float(level[3]),
                "percentage": float(level[4]),
                "shares_quantity": float(level[5]),
                "status": level[6],
                "symbol": level[7],
                "action": level[8]
            })
        
        # Get all active stop loss levels for the user
        cursor.execute("""
            SELECT 
                sl.id, sl.trade_id, sl.price, sl.status, 
                t.symbol, t.action, t.quantity
            FROM stop_loss_levels sl
            JOIN trades t ON sl.trade_id = t.id
            WHERE t.user_id = %s AND sl.status = 'active'
            ORDER BY t.symbol
        """, (current_user.id,))
        
        sl_levels = cursor.fetchall()
        stop_loss_monitoring = []
        
        for level in sl_levels:
            # Calculate remaining shares (total shares minus executed take profit levels)
            cursor.execute("""
                SELECT COALESCE(SUM(shares_quantity), 0) as executed_shares
                FROM take_profit_levels 
                WHERE trade_id = %s AND status = 'executed'
            """, (level[1],))
            executed_tp_shares = cursor.fetchone()[0]
            remaining_shares = float(level[6]) - float(executed_tp_shares)
            
            stop_loss_monitoring.append({
                "id": level[0],
                "trade_id": level[1],
                "price": float(level[2]),
                "status": level[3],
                "symbol": level[4],
                "action": level[5],
                "remaining_shares": remaining_shares
            })
        
        return {
            "take_profit_levels": take_profit_monitoring,
            "stop_loss_levels": stop_loss_monitoring,
            "total_tp_levels": len(take_profit_monitoring),
            "total_sl_levels": len(stop_loss_monitoring)
        }
        
    except Exception as e:
        print(f"Error getting monitoring levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    # Get port from environment variable (for Render) or default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False) 