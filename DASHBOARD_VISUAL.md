# Dashboard Visual Layout

## What You'll See Now

```
┌─────────────────────────────────────────────────────────────────────┐
│ Dashboard                                    [Sync Dashboard] 🔄      │
│                                             Last sync: 2:45:30       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ℹ️ Active Account: My Trading Account (paper)                        │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │ Total Trades    │ │ Win Rate        │ │ Total P&L       │ │ Pending Signals │ │
│ │      10         │ │    66.7%        │ │   +$1,250.50    │ │       5        │ │
│ │ 3 open, 1 pend │ │    4W / 2L      │ │  Avg: $208.42   │ │ Waiting...     │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                                                                      │
│ Signal Statistics                                                    │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐      │
│ │ Total Signals   │ │ Approved        │ │ Executed        │      │
│ │      25         │ │      15         │ │      12         │      │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘      │
│                                                                      │
│ Recent Signals                                                       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ • BUY AAPL @ 150.00  [Pending]           [Approve] [Reject]     │ │
│ │ • SELL TSLA @ 195.50 [Pending]           [Approve] [Reject]     │ │
│ │ • BUY MSFT @ 380.00  [Pending]           [Approve] [Reject]     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Recent Trades                                                        │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Symbol  Action  Qty   Entry    Current   P&L      Status        │ │
│ │ AAPL    BUY     100   149.50   150.25   +$75.00  Open   [Close]│ │
│ │ TSLA    SELL    50    196.00   195.50   +$25.00  Open   [Close]│ │
│ │ MSFT    BUY     75    378.50   380.00   +$112.50 Open   [Close]│ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Improvements

### 1. 🎯 Pending Signals Front & Center
- Big yellow card shows pending signal count
- Can't miss signals waiting for approval

### 2. 📊 Complete Trade Overview
- Total trades with open/pending breakdown
- Win rate based on closed trades only
- Color-coded P&L (green for profit, red for loss)

### 3. 🔄 Auto-Sync Like Trades Page
- Sync button in header
- Auto-syncs every 30 seconds
- Shows last sync time

### 4. 📈 Signal Flow Visibility
```
Total Signals (25) → Approved (15) → Executed (12)
                  → Rejected (5)
                  → Pending (5) ← YOU ARE HERE
```

### 5. 🏦 Account Awareness
- Shows which account you're viewing
- All data filtered by active account
- No confusion about which trades are shown

## Color Coding

- 🟨 **Yellow** - Pending (needs action)
- 🟩 **Green** - Positive/Approved/Profit
- 🟥 **Red** - Negative/Rejected/Loss
- 🟦 **Blue** - Active/Open
- ⬜ **Gray** - Closed/Completed

The dashboard now gives you everything at a glance with pending signals prominently displayed! 