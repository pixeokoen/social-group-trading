from fastapi import FastAPI, Depends, HTTPException, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime
import json
import hashlib
import hmac
import os
from decimal import Decimal
import secrets
import asyncio
from jose import JWTError, jwt
from contextlib import asynccontextmanager

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
                        api_secret=account[2],
                        paper=(account[3] == 'paper')
                    )
                    
                    # Sync trades for this account
                    cursor.execute("""
                        SELECT id, broker_order_id, symbol
                        FROM trades 
                        WHERE account_id = %s 
                        AND status = 'pending'
                        AND broker_order_id IS NOT NULL
                    """, (account[0],))
                    
                    pending_trades = cursor.fetchall()
                    
                    for trade in pending_trades:
                        try:
                            # Get order status
                            order_status = await client.get_order_status(trade[1])
                            
                            if order_status and order_status['status'] == 'filled':
                                # Update trade with float conversion
                                fill_price = float(order_status.get('filled_avg_price', 0))
                                cursor.execute("""
                                    UPDATE trades 
                                    SET status = 'open',
                                        broker_fill_price = %s,
                                        entry_price = %s,
                                        opened_at = %s
                                    WHERE id = %s
                                """, (
                                    fill_price,
                                    fill_price,
                                    order_status.get('filled_at'),
                                    trade[0]
                                ))
                                
                                print(f"Auto-sync: Trade {trade[2]} filled at ${fill_price}")
                        except Exception as e:
                            print(f"Error syncing trade {trade[0]}: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error syncing account {account[0]}: {e}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error in auto-sync: {e}")
            if 'conn' in locals():
                conn.close()
        
        # Wait 30 seconds before next sync
        await asyncio.sleep(30)

# Lifespan context manager for background tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting background trade sync...")
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", os.getenv("FRONTEND_URL", "")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
            api_secret=account.api_secret,
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
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'manual_entry', 'approved')
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
        
        # Calculate estimated cost
        if order_type == 'MARKET':
            estimated_price = market_data.get('last', 0)
        else:
            estimated_price = float(limit_price) if limit_price else market_data.get('last', 0)
        
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
        
        # If signals were found, save them to the database
        if analysis_result.get("is_signal") and analysis_result.get("signals"):
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                
                # Extract signals for database
                db_signals = message_analyzer.extract_signals_for_db(analysis_result)
                
                for signal_data in db_signals:
                    cursor.execute("""
                        INSERT INTO signals (
                            user_id, symbol, action, price, 
                            stop_loss, take_profit, source, 
                            original_message, remarks, analysis_notes, status
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                        RETURNING id
                    """, (
                        current_user.id,
                        signal_data['symbol'],
                        signal_data['action'],
                        signal_data.get('price'),
                        signal_data.get('stop_loss'),
                        signal_data.get('take_profit'),
                        'message_paste',
                        signal_data.get('original_message', ''),
                        signal_data.get('remarks', ''),
                        signal_data.get('analysis_notes', '')
                    ))
                    
                    signal_id = cursor.fetchone()[0]
                    print(f"Created signal {signal_id} from AI analysis")
                
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Error saving analyzed signals: {e}")
                # Don't fail the request, just log the error
            finally:
                conn.close()
        
        return MessageAnalysisResponse(**analysis_result)
        
    except Exception as e:
        print(f"Error analyzing message: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

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
            SELECT * FROM trades 
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
            
            # Convert Decimal to float for JSON serialization
            for field in ['entry_price', 'exit_price', 'current_price', 'pnl', 
                          'floating_pnl', 'broker_fill_price']:
                if field in trade_dict and trade_dict[field] is not None:
                    trade_dict[field] = float(trade_dict[field])
            
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
            time_in_force = order_params.get('time_in_force', 'DAY')
        else:
            quantity = signal_dict.get('quantity') or 100
            order_type = 'LMT' if signal_dict.get('price') else 'MKT'
            limit_price = float(signal_dict['price']) if signal_dict.get('price') else None
            time_in_force = 'DAY'
        
        # Ensure quantity is a float for fractional shares
        quantity = float(quantity)
        
        # Convert order type to Alpaca format
        alpaca_order_type = 'limit' if order_type in ['LIMIT', 'LMT'] else 'market'
        
        # Validate with broker (check account balance, etc.)
        account_summary = await broker_client.get_account_summary()
        buying_power = account_summary.get('BuyingPower', 0)
        
        # Calculate required capital (simplified)
        if alpaca_order_type == 'market':
            # Get current market price for validation
            market_data = await broker_client.get_market_data(signal_dict['symbol'])
            estimated_price = market_data.get('last', 0)
        else:
            estimated_price = float(limit_price) if limit_price else 0
            
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
            limit_price or estimated_price or 0, str(order_id), datetime.utcnow()  # Ensure order_id is string
        ))
        
        trade_id = cursor.fetchone()[0]
        
        # Update signal status and add account_id
        cursor.execute(
            "UPDATE signals SET status = 'executed', account_id = %s WHERE id = %s",
            (account.id, signal_id)
        )
        
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
        
        # Trading statistics for the active account
        # Include all trades (open, closed, pending) for total count
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                COUNT(CASE WHEN status = 'open' THEN 1 END) as open_trades,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_trades,
                COUNT(CASE WHEN status = 'closed' AND pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN status = 'closed' AND pnl < 0 THEN 1 END) as losing_trades,
                COALESCE(SUM(CASE WHEN status = 'closed' THEN pnl ELSE 0 END), 0) as total_pnl,
                COALESCE(AVG(CASE WHEN status = 'closed' THEN pnl ELSE NULL END), 0) as avg_pnl,
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
            # Convert Decimal to float
            for field in ['entry_price', 'current_price', 'floating_pnl', 'pnl']:
                if trade_dict.get(field) is not None:
                    trade_dict[field] = float(trade_dict[field])
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
        
        # Calculate win rate based on closed trades only
        closed_trades = analytics['winning_trades'] + analytics['losing_trades']
        if closed_trades > 0:
            analytics['win_rate'] = (analytics['winning_trades'] / closed_trades) * 100
        else:
            analytics['win_rate'] = 0
        
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
        
        # Get all pending trades for this account
        cursor.execute("""
            SELECT id, broker_order_id, symbol, quantity, action
            FROM trades 
            WHERE user_id = %s AND account_id = %s 
            AND status IN ('pending', 'open')
            AND broker_order_id IS NOT NULL
        """, (current_user.id, account.id))
        
        pending_trades = cursor.fetchall()
        updated_count = 0
        
        for trade in pending_trades:
            trade_id, order_id, symbol, quantity, action = trade
            
            try:
                # Get order status from Alpaca
                order_status = await broker_client.get_order_status(order_id)
                
                if order_status:
                    alpaca_status = order_status['status']
                    
                    # Map Alpaca status to our status
                    if alpaca_status == 'filled':
                        # Update trade with fill information
                        cursor.execute("""
                            UPDATE trades 
                            SET status = 'open',
                                broker_fill_price = %s,
                                entry_price = %s,
                                opened_at = %s
                            WHERE id = %s
                        """, (
                            float(order_status.get('filled_avg_price', 0)),
                            float(order_status.get('filled_avg_price', 0)),
                            order_status.get('filled_at'),
                            trade_id
                        ))
                        updated_count += 1
                        
                    elif alpaca_status == 'partially_filled':
                        # Update with partial fill info
                        filled_qty = order_status.get('filled_qty', 0)
                        cursor.execute("""
                            UPDATE trades 
                            SET status = 'open',
                                broker_fill_price = %s,
                                entry_price = %s,
                                quantity = %s,
                                opened_at = %s
                            WHERE id = %s
                        """, (
                            float(order_status.get('filled_avg_price', 0)),
                            float(order_status.get('filled_avg_price', 0)),
                            filled_qty,
                            order_status.get('filled_at'),
                            trade_id
                        ))
                        updated_count += 1
                        
                    elif alpaca_status in ['canceled', 'expired', 'rejected']:
                        # Mark trade as cancelled
                        cursor.execute("""
                            UPDATE trades 
                            SET status = 'cancelled',
                                close_reason = %s
                            WHERE id = %s
                        """, (f"Order {alpaca_status}", trade_id))
                        updated_count += 1
                        
            except Exception as e:
                print(f"Error syncing trade {trade_id}: {e}")
                # Continue with other trades
                continue
        
        # Also sync current positions from Alpaca
        try:
            positions = await broker_client.get_positions()
            
            # Update current prices for open trades
            for position in positions:
                current_price = float(position.get('current_price', 0))
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
                    current_price,
                    current_price,
                    current_price,
                    position['symbol'],
                    current_user.id,
                    account.id
                ))
        except Exception as e:
            print(f"Error syncing positions: {e}")
            positions = []
        
        conn.commit()
        
        return {
            "message": "Sync completed",
            "trades_updated": updated_count,
            "positions_synced": len(positions)
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error syncing trades: {e}")
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

if __name__ == "__main__":
    # Get port from environment variable (for Render) or default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False) 