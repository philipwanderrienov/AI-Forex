-- DBeaver: koneksi forex_intelligence, Execute SQL Script (Alt+X).
-- Read-only. Tidak mengubah candle, timezone database, checkpoint, atau quarantine.
-- Default: delapan hari terakhir seperti lookback API. Untuk investigasi ulang,
-- ganti as_of_utc dengan TIMESTAMPTZ eksplisit dari snapshot API yang dibandingkan.
-- UTC+3 hanya HIPOTESIS untuk periode September 2026; bukan aturan DST historis.
-- Sesi XAUUSD dari screenshot: Senin-Jumat 00:00-23:00 waktu broker.

BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '30s';

DO $TARGET$
BEGIN
    IF current_database() <> 'forex_intelligence' THEN
        RAISE EXCEPTION 'Target database salah: %, seharusnya forex_intelligence.', current_database();
    END IF;
END $TARGET$;

WITH parameters AS (
    SELECT CURRENT_TIMESTAMP AS as_of_utc,
           INTERVAL '8 days' AS lookback,
           INTERVAL '3 hours' AS assumed_broker_offset
), observations AS (
    SELECT c."OpenTime" AS open_time,
           c."CloseTime" AS close_time,
           lag(c."OpenTime") OVER (ORDER BY c."OpenTime") AS previous_open
    FROM public.candles c
    CROSS JOIN parameters p
    WHERE c."Instrument" = 'XAUUSD'
      AND c."Timeframe" = 'H1'
      AND c."Status" = 'Final'
      AND c."OpenTime" >= p.as_of_utc - p.lookback
      AND c."OpenTime" <= p.as_of_utc
), coverage AS (
    SELECT count(*) AS candle_count,
           min(open_time) AS first_open,
           max(open_time) AS last_open,
           max(close_time) AS last_close
    FROM observations
), intervals AS (
    SELECT previous_open, open_time AS next_open,
           extract(epoch FROM (open_time - previous_open)) / 3600 AS distance_hours,
           mod(extract(epoch FROM (open_time - previous_open)), 3600) <> 0 AS irregular_alignment
    FROM observations
    WHERE open_time - previous_open > INTERVAL '1 hour'
), slots AS (
    SELECT i.previous_open, i.next_open, s.expected_open,
           s.expected_open AT TIME ZONE 'UTC' AS utc_clock,
           (s.expected_open AT TIME ZONE 'UTC') + p.assumed_broker_offset AS broker_clock
    FROM intervals i
    CROSS JOIN parameters p
    CROSS JOIN LATERAL generate_series(
        i.previous_open + INTERVAL '1 hour',
        i.next_open - INTERVAL '1 microsecond',
        INTERVAL '1 hour'
    ) AS s(expected_open)
), classified AS (
    SELECT *,
           CASE extract(isodow FROM utc_clock)
               WHEN 6 THEN false
               WHEN 7 THEN utc_clock::time >= TIME '22:00'
               WHEN 5 THEN utc_clock::time < TIME '22:00'
               ELSE true
           END AS api_expects_candle,
           extract(isodow FROM broker_clock) BETWEEN 1 AND 5
               AND broker_clock::time < TIME '23:00' AS hypothesis_expects_candle
    FROM slots
), gap_counts AS (
    SELECT previous_open, next_open,
           count(*) AS absent_hourly_slots,
           count(*) FILTER (WHERE api_expects_candle) AS api_gap_slots,
           count(*) FILTER (WHERE NOT hypothesis_expects_candle) AS hypothesis_closed_slots,
           count(*) FILTER (WHERE hypothesis_expects_candle) AS hypothesis_open_missing_slots,
           count(*) FILTER (WHERE api_expects_candle AND NOT hypothesis_expects_candle)
               AS api_slots_explained_by_hypothesis,
           min(expected_open) FILTER (WHERE hypothesis_expects_candle) AS first_open_missing
    FROM classified
    GROUP BY previous_open, next_open
)
SELECT 'XAUUSD H1' AS series,
       p.as_of_utc AT TIME ZONE 'Asia/Jakarta' AS as_of_wib,
       (p.as_of_utc - p.lookback) AT TIME ZONE 'Asia/Jakarta' AS window_start_wib,
       c.candle_count,
       c.first_open AT TIME ZONE 'Asia/Jakarta' AS first_stored_open_wib,
       c.last_open AT TIME ZONE 'Asia/Jakarta' AS last_stored_open_wib,
       c.last_close AT TIME ZONE 'Asia/Jakarta' AS last_stored_close_wib,
       CASE WHEN c.candle_count < 2 THEN 'INSUFFICIENT_DATA'
            WHEN i.previous_open IS NULL THEN 'NO_INTERNAL_GAPS'
            WHEN i.irregular_alignment THEN 'CHECK_TIMESTAMP_ALIGNMENT'
            WHEN g.hypothesis_open_missing_slots > 0 THEN 'COMPARE_WITH_MT5_HISTORY'
            ELSE 'CLOSED_UNDER_UTC_PLUS_3_HYPOTHESIS'
       END AS diagnostic,
       i.previous_open AT TIME ZONE 'Asia/Jakarta' AS previous_open_wib,
       (i.previous_open + INTERVAL '1 hour') AT TIME ZONE 'Asia/Jakarta' AS first_absent_slot_wib,
       i.next_open AT TIME ZONE 'Asia/Jakarta' AS next_open_wib,
       i.distance_hours,
       i.irregular_alignment,
       g.absent_hourly_slots,
       g.api_gap_slots,
       g.hypothesis_closed_slots,
       g.hypothesis_open_missing_slots,
       g.api_slots_explained_by_hypothesis,
       g.first_open_missing AT TIME ZONE 'Asia/Jakarta' AS first_open_missing_wib,
       coalesce(sum(g.api_gap_slots) OVER (), 0) AS total_api_gap_slots,
       coalesce(sum(g.hypothesis_open_missing_slots) OVER (), 0) AS total_hypothesis_open_missing_slots
FROM parameters p
CROSS JOIN coverage c
LEFT JOIN intervals i ON true
LEFT JOIN gap_counts g ON g.previous_open = i.previous_open AND g.next_open = i.next_open
ORDER BY i.previous_open;

COMMIT;
