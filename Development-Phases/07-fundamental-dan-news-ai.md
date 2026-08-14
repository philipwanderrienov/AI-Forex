# Fase 07 — Fundamental, News Intelligence, dan AI Advisor

## Tujuan

Memperkaya analisis dengan konteks ekonomi dan berita tanpa membiarkan output AI menggantikan fakta, formula, atau kontrol risiko.

## Pekerjaan economic data

- Integrasikan economic calendar dan satu sumber data makro.
- Normalisasi negara, mata uang, indikator, periode, actual, forecast, previous, unit, dan importance.
- Simpan `scheduledAt`, `publishedAt`, `receivedAt`, dan revision history.
- Buat surprise score dengan memperhatikan unit dan arah baik/buruk setiap indikator.
- Mapping event ke mata uang dan periode dampak.
- Tambahkan proximity/embargo ke Risk Engine.

## Pekerjaan news pipeline

- Integrasikan satu sumber berita terlebih dahulu.
- Normalisasi title, body/summary, source, URL canonical, published time, dan received time.
- Deduplicate berdasarkan URL, fingerprint, dan semantic similarity bila diperlukan.
- Pisahkan berita asli, pembaruan artikel, dan berita sindikasi.
- Simpan attribution dan patuhi ketentuan lisensi sumber.

## LLM classification

- Gunakan structured output/JSON schema untuk currency affected, category, sentiment, impact, direction, duration, dan confidence.
- Batasi nilai enum dan validasi semua response sebelum disimpan.
- Simpan provider/model, prompt version, latency, token/cost, dan raw response yang aman untuk audit.
- Terapkan retry terbatas, timeout, circuit breaker, dan fallback `unclassified`.
- Lindungi prompt dari instruksi yang terdapat dalam isi berita.
- Buat dataset berlabel manusia untuk evaluasi precision/recall serta agreement.

## Fundamental dan news scoring

- Definisikan decay berdasarkan usia dan tipe berita.
- Pisahkan fakta ekonomi, interpretasi berita, dan skor agregat.
- Cegah double-counting satu event dari banyak artikel.
- Masukkan skor ke Market Brain dengan bobot versioned dan conflict handling.
- Jika layanan AI gagal, sistem tetap menghasilkan technical view dengan status konteks AI tidak tersedia.

## AI Advisor

- Input hanya menggunakan snapshot/evidence yang telah divalidasi.
- Output: `BUY/SELL/WAIT`, ringkasan alasan, invalidation, dan warnings.
- Arah akhir harus tunduk pada hard rule Risk Engine; AI tidak dapat mengubah `REJECTED` menjadi rekomendasi aktif.
- Validasi agar penjelasan tidak menyebut angka atau fakta yang tidak ada pada input.
- Tampilkan evidence source dan waktu informasi kepada pengguna.

## Tentang vector database

Mulai dengan PostgreSQL dan full-text search. Tambahkan vector database hanya jika use case seperti semantic retrieval artikel historis mempunyai peningkatan kualitas yang terukur.

## Kriteria selesai

- Event dan berita dapat ditelusuri ke sumber serta waktu penerimaan.
- Structured output invalid tidak masuk ke scoring.
- Evaluasi klasifikasi mencapai threshold yang ditentukan di fase 00.
- Gangguan AI tidak menghentikan market pipeline atau menghilangkan kontrol risiko.
- UI memperlihatkan kontribusi fundamental/news secara terpisah dan transparan.

