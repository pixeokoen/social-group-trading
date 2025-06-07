-- ================================================================
-- SELL ALL FEATURE - Database Schema Updates
-- ================================================================
-- This script adds support for the "Sell All" feature including:
-- 1. New status 'cancelled_by_sell_all' for TP/SL levels
-- 2. Override tracking fields (price and date)
-- ================================================================

-- 1. Update take_profit_levels table
-- ----------------------------------------------------------------

-- Drop existing constraint
ALTER TABLE take_profit_levels 
DROP CONSTRAINT IF EXISTS take_profit_levels_status_check;

-- Add new constraint with cancelled_by_sell_all status
ALTER TABLE take_profit_levels 
ADD CONSTRAINT take_profit_levels_status_check 
CHECK (status IN ('pending', 'executed', 'cancelled', 'cancelled_by_sell_all'));

-- Add override tracking columns
ALTER TABLE take_profit_levels 
ADD COLUMN IF NOT EXISTS override_price DECIMAL(10,2);

ALTER TABLE take_profit_levels 
ADD COLUMN IF NOT EXISTS override_date TIMESTAMP;

-- 2. Update stop_loss_levels table
-- ----------------------------------------------------------------

-- Drop existing constraint
ALTER TABLE stop_loss_levels 
DROP CONSTRAINT IF EXISTS stop_loss_levels_status_check;

-- Add new constraint with cancelled_by_sell_all status
ALTER TABLE stop_loss_levels 
ADD CONSTRAINT stop_loss_levels_status_check 
CHECK (status IN ('active', 'executed', 'cancelled', 'cancelled_by_sell_all'));

-- Add override tracking columns
ALTER TABLE stop_loss_levels 
ADD COLUMN IF NOT EXISTS override_price DECIMAL(10,2);

ALTER TABLE stop_loss_levels 
ADD COLUMN IF NOT EXISTS override_date TIMESTAMP;

-- ================================================================
-- Verification queries (optional - run to verify changes)
-- ================================================================

-- Check table structures
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'take_profit_levels' 
-- ORDER BY ordinal_position;

-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'stop_loss_levels' 
-- ORDER BY ordinal_position;

-- Check constraints
-- SELECT constraint_name, check_clause 
-- FROM information_schema.check_constraints 
-- WHERE constraint_name LIKE '%status_check';

-- ================================================================
-- COMPLETED SUCCESSFULLY ✅
-- ================================================================ 