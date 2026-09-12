-- DBeaver: forex_intelligence, Execute SQL Script (Alt+X). Read-only.
-- Ledger maxima alone are not a complete sequence floor: also inspect pending
-- spool, quarantine, the stopped terminal's Global Variable and guard file.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '30s';
DO $TARGET$
BEGIN
    IF current_database() <> 'forex_intelligence' THEN
        RAISE EXCEPTION 'Target database salah: %, seharusnya forex_intelligence.', current_database();
    END IF;
END $TARGET$;

SELECT "SourceInstanceId",
       count(*) AS batch_count,
       min("Sequence") AS first_sequence,
       max("Sequence") AS last_sequence,
       min("StoredAt") AT TIME ZONE 'Asia/Jakarta' AS first_stored_wib,
       max("StoredAt") AT TIME ZONE 'Asia/Jakarta' AS last_stored_wib
FROM public.market_data_batches
GROUP BY "SourceInstanceId"
ORDER BY "SourceInstanceId";

SELECT "Sequence", "BatchId", "Checksum", "RecordCount",
       "StoredAt" AT TIME ZONE 'Asia/Jakarta' AS stored_at_wib
FROM public.market_data_batches
WHERE "SourceInstanceId" = 'antix-mt5-primary'
  AND "Sequence" IN (1, 118, 358, 359)
ORDER BY "Sequence";
COMMIT;
