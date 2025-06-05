-- Fix signals source constraint to match the Signal model values
-- Drop the old constraint
ALTER TABLE signals DROP CONSTRAINT IF EXISTS signals_source_check;

-- Add the new constraint with all allowed source values
ALTER TABLE signals ADD CONSTRAINT signals_source_check 
CHECK (source IN ('manual', 'manual_entry', 'message_paste', 'whatsapp', 'telegram', 'discord'));

-- Show current constraint
SELECT constraint_name, check_clause 
FROM information_schema.check_constraints 
WHERE table_name = 'signals' AND constraint_name = 'signals_source_check'; 