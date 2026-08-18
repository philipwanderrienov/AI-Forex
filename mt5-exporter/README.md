# MT5 Read-only Exporter

`ForexIntelligenceDataExporter.mq5` pada Fase 01 hanya mengirim heartbeat ke Python bridge. Source tidak mempunyai fungsi membuka, mengubah, atau menutup order.

Sebelum menjalankan EA:

1. Jalankan Python bridge.
2. Tambahkan `http://127.0.0.1:8001` ke daftar allowed WebRequest MT5.
3. Compile source melalui MetaEditor.
4. Pasang EA pada satu chart akun demo.
5. Periksa log EA dan response `202` dari bridge.

Data tick, candle, account snapshot, authentication, dan retry ditambahkan bertahap pada Fase 02 setelah heartbeat terbukti stabil.
