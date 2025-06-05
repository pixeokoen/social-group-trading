from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, Dict, Any, List
from decimal import Decimal

# User models
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True

# WhatsApp Message models
class WhatsAppMessage(BaseModel):
    id: int
    raw_message: str
    sender: str
    group_name: str
    timestamp: datetime
    processed: bool = False
    is_signal: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

# Account models
class AccountBase(BaseModel):
    name: str
    account_type: Literal["paper", "live"]
    broker: Literal["alpaca", "ibkr"]
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    is_active: bool = True
    is_default: bool = False

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class Account(AccountBase):
    id: int
    user_id: int
    created_at: datetime
    realized_pnl: Optional[Decimal] = 0
    realized_pnl_updated_at: Optional[datetime] = None
    win_rate: Optional[float] = 0
    
    class Config:
        from_attributes = True

# User session model
class UserSession(BaseModel):
    user_id: int
    active_account_id: Optional[int] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Signal models
class SignalBase(BaseModel):
    symbol: str
    action: Literal["BUY", "SELL"]
    quantity: Optional[int] = None
    price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    source: Literal["manual_entry", "message_paste", "whatsapp", "telegram", "discord"] = "manual_entry"
    original_message: Optional[str] = None
    remarks: Optional[str] = None
    analysis_notes: Optional[str] = None
    enhanced_data: Optional[Dict[str, Any]] = None

class SignalCreate(SignalBase):
    pass

class Signal(SignalBase):
    id: int
    user_id: Optional[int] = None
    account_id: Optional[int] = None
    whatsapp_message_id: Optional[int] = None
    created_at: datetime
    status: Literal["pending", "approved", "rejected", "executed"] = "pending"
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    
    class Config:
        from_attributes = True

# Trade models
class TradeBase(BaseModel):
    symbol: str
    action: Literal["BUY", "SELL"]
    quantity: Decimal
    entry_price: Decimal

class TradeCreate(TradeBase):
    signal_id: Optional[int] = None

class Trade(TradeBase):
    id: int
    user_id: int
    account_id: Optional[int] = None
    signal_id: Optional[int] = None
    exit_price: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    pnl: Optional[Decimal] = None
    floating_pnl: Optional[Decimal] = None
    status: Literal["pending", "open", "closed", "cancelled"] = "pending"
    created_at: datetime
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    broker_order_id: Optional[str] = None
    broker_fill_price: Optional[Decimal] = None
    close_reason: Optional[str] = None
    
    class Config:
        from_attributes = True

# Analytics model
class Analytics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: Decimal
    avg_pnl: Decimal
    win_rate: float
    avg_trade_duration: Optional[float] = None
    total_signals: int
    approved_signals: int
    rejected_signals: int
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

# Token model for authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# WHAPI Webhook models
class WHAPIWebhook(BaseModel):
    event: Dict[str, Any]
    instanceId: str
    timestamp: int
    
class SignalApproval(BaseModel):
    approved: bool
    notes: Optional[str] = None

class TradeClose(BaseModel):
    close_price: Optional[Decimal] = None
    reason: Optional[str] = None

# Message Analysis models
class MessageAnalysisRequest(BaseModel):
    message: str

class MessageAnalysisResponse(BaseModel):
    is_signal: bool
    signals: list[dict]
    original_message: str
    analysis_notes: str

# Signal Source models
class SignalSourceBase(BaseModel):
    source_type: Literal["whapi", "telegram", "discord"]
    source_identifier: str  # Can be used for channel name/description
    name: str
    description: Optional[str] = None
    is_active: bool = True
    filter_config: Dict[str, Any] = {}  # Will include chat_id filter

class SignalSourceCreate(SignalSourceBase):
    account_ids: List[int] = []  # Accounts to route signals to
    auto_approve: Dict[int, bool] = {}  # Map of account_id to auto_approve setting

class SignalSourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    filter_config: Optional[Dict[str, Any]] = None
    account_ids: Optional[List[int]] = None
    auto_approve: Optional[Dict[int, bool]] = None

class SignalSource(SignalSourceBase):
    id: int
    user_id: int
    webhook_token: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    accounts: List[Dict[str, Any]] = []  # List of accounts with auto_approve flag
    
    class Config:
        from_attributes = True

class SourceAccountMapping(BaseModel):
    source_id: int
    account_id: int
    auto_approve: bool = False
    account_name: Optional[str] = None
    account_type: Optional[str] = None
    
    class Config:
        from_attributes = True 