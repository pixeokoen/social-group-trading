-- Fix exit prices for existing closed trades
-- This script sets exit_price from current_price or broker_fill_price for closed trades

UPDATE trades 
SET exit_price = COALESCE(broker_fill_price, current_price, entry_price)
WHERE status = 'closed' 
  AND exit_price IS NULL 
  AND COALESCE(broker_fill_price, current_price, entry_price) IS NOT NULL;

-- Clear current_price for closed trades (it should only be for open trades)
UPDATE trades 
SET current_price = NULL
WHERE status = 'closed';

-- Show the results
SELECT 
    id,
    symbol,
    action,
    status,
    quantity,
    entry_price,
    exit_price,
    current_price,
    pnl,
    floating_pnl
FROM trades 
WHERE status = 'closed'
ORDER BY id DESC
LIMIT 10; 