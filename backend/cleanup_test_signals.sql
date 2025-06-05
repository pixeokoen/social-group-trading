-- Clean up test signals that were automatically created during analysis testing
-- This script removes signals with source 'manual' (from message analysis), 'message_analysis' or 'message_paste' from recent testing

-- Show signals that will be deleted (for review)
SELECT 
    id, symbol, action, source, created_at, original_message, analysis_notes
FROM signals 
WHERE (
    source IN ('message_analysis', 'message_paste') 
    OR (source = 'manual' AND analysis_notes IS NOT NULL AND analysis_notes != '')
)
AND created_at > NOW() - INTERVAL '1 day'
ORDER BY created_at DESC;

-- Uncomment the line below AFTER reviewing the above results to actually delete them
-- DELETE FROM signals WHERE (source IN ('message_analysis', 'message_paste') OR (source = 'manual' AND analysis_notes IS NOT NULL AND analysis_notes != '')) AND created_at > NOW() - INTERVAL '1 day';

-- Show remaining signals after cleanup
-- SELECT COUNT(*) as remaining_signals FROM signals; 