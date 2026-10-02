# ⚔️ NASH TAKTIK (@nashtaktik) — Automated Media Pipeline

Pipeline produksi dan distribusi multi-platform otomatis untuk kanal **Nash Taktik & Sejarah** (`@nashtaktik`), berfokus pada analisis strategi militer kuno, taktik perang asimetris, dan sejarah peradaban dunia.

---

## 🏛️ Arsitektur Piramida Mingguan (Weekly Content Pyramid)

Kanal beroperasi dengan model piramida 1 Long-Form + 6 Daily Shorts:

```
                          ┌───────────────────────────┐
                          │   MINGGU (19:00 WIB)      │
                          │   Long-Form Documentary   │
                          │   Durasi: 7–10 Menit      │
                          │   YouTube, TikTok, IG     │
                          └─────────────┬─────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
┌──────────────────────────┐                             ┌──────────────────────────┐
│   SENIN s/d RABU (07:00) │                             │  KAMIS s/d SABTU (07:00) │
│   • Senin: Fatal Blunder │                             │  • Kamis: Weapon Secret  │
│   • Selasa: Pincer Move  │                             │  • Jumat: Psychology     │
│   • Rabu: Carnage/Impact │                             │  • Sabtu: Creed/Doctrine │
└──────────────────────────┘                             └──────────────────────────┘
```

1. **Long-Form (Minggu, 19:00 WIB)**: Dokumenter sejarah taktis mendalam beresolusi 1080p, animasi peta taktis HyperFrames v3, visual AI sinematik faceless, dan audio orkestra resmi *The Weight of the Shield.mp3*.
2. **Daily Shorts (Senin–Sabtu, 07:00 WIB)**: Video vertikal 1080x1920 format *Dual-Stack Tactical Layout* (Atas: Peta Taktis gerak, Bawah: Sinematik faceless, Tengah: Gold ribbon title banner, Subtitle ASS dengan penyorotan kata kunci kinetik).

---

## ⚙️ Model Operasi: Local Buffer vs Cloud Autonomous

### 1. Long-Form Video (Asinkron / Waktu Luang)
- Dikerjakan secara fleksibel di waktu luang di komputer lokal tanpa tekanan deadline harian.
- Menggunakan skrip `scripts/publish_long.py`:
  - **Opsi Rilis Langsung**: `python scripts/publish_long.py --video path/to/video.mp4 --title "..." --desc "..."`
  - **Opsi Penjadwalan Cloud (Scheduled)**: Menjadwalkan video tayang di masa depan menggunakan parameter `--schedule "2026-10-08T12:00:00Z"`. Video langsung terunggah dan disimpan di server YouTube dalam status `private` hingga jadwal rilis tiba.

### 2. Daily Shorts (100% Otomatis Cloud via GitHub Actions)
- Dijalankan secara otomatis oleh GitHub Actions Cron setiap Senin sampai Sabtu pukul **00:00 UTC (07:00 WIB / 08:00 WITA)**.
- Alur kerja cloud:
  1. Membaca naskah paket harian di `curriculum/week_XXX/short_XX_hari.json`.
  2. Mensintesis narasi suara berwibawa via Edge TTS `id-ID-ArdiNeural` (+5% rate).
  3. Menghasilkan subtitle ASS kinetik dengan highlight kata kunci.
  4. Merender video vertikal Dual-Stack 1080x1920 dalam waktu ~30 detik menggunakan FFmpeg single-pass.
  5. Mempublikasikan serentak ke **YouTube Shorts** (dengan backlink ke video panjang terkait), serta **TikTok** dan **Instagram Reels** via Zernio API.
  6. Mengirim laporan hasil tayang ke Telegram Owner.
  7. Mencatat riwayat publikasi dan meng-commit pembaruan status ke branch `main`.

---

## 🔐 Konfigurasi GitHub Repository Secrets

Agar GitHub Actions dapat melakukan render dan auto-posting, tambahkan rahasia berikut di **Settings → Secrets and variables → Actions → New repository secret**:

| Nama Secret | Deskripsi |
| :--- | :--- |
| `GOOGLE_CLIENT_ID` | OAuth Client ID Google Cloud Project `@nashtaktik` |
| `GOOGLE_CLIENT_SECRET` | OAuth Client Secret Google Cloud Project `@nashtaktik` |
| `YT_REFRESH_TOKEN` | Refresh Token YouTube Data API v3 untuk akun `@nashtaktik` |
| `ZERNIO_API_KEY` | API Key resmi Zernio untuk publikasi TikTok & Instagram |
| `TIKTOK_ACCOUNT_ID` | ID akun TikTok di Zernio (`6abbb2e6694b468f723ea3a4`) |
| `INSTAGRAM_ACCOUNT_ID` | ID akun Instagram di Zernio (`6abbb38ad9cc457b83f314fc`) |
| `BOT_TOKEN` | *(Opsional)* Telegram Bot Token untuk notifikasi |
| `OWNER_CHAT_ID` | *(Opsional)* Telegram Chat ID Owner penerima laporan |

---

## 📁 Struktur Repositori

```
nashtaktik/
├── .github/workflows/
│   ├── daily-shorts.yml          # Runner Cron harian otomatis (Senin-Sabtu)
│   └── publish-long.yml          # Workflow manual untuk publish/schedule long-form
├── curriculum/
│   ├── MASTER_SCHEDULE.json       # Master rencana 26 pekan & topik pertempuran
│   └── week_001/                  # Paket minggu ke-1: Pertempuran Marathon (490 SM)
│       ├── long_form.json         # Metadata & URL video panjang rilis
│       ├── short_01_senin.json    # Paket Short 01 (Blunder Kavaleri)
│       ├── short_02_selasa.json   # Paket Short 02 (Trik Sayap Tebal)
│       ├── short_03_rabu.json     # Paket Short 03 (Pembantaian Rawa)
│       ├── short_04_kamis.json    # Paket Short 04 (Aspis vs Sparabara)
│       ├── short_05_jumat.json    # Paket Short 05 (Serbuan Lari 1,5 km)
│       ├── short_06_sabtu.json    # Paket Short 06 (Filosofi Miltiades)
│       └── images/                # Aset gambar taktis & sinematik faceless
├── assets/
│   └── audio/
│       └── The Weight of the Shield.mp3  # BGM resmi orkestra
├── scripts/
│   ├── generate_voiceover.py      # Sintesis Edge TTS ArdiNeural
│   ├── generate_subtitles.py      # Generator subtitle ASS Dual-Stack
│   ├── render_short.py            # FFmpeg Single-pass Dual-Stack 1080x1920
│   ├── publish_short.py           # Multi-platform distributor (YT + Zernio)
│   ├── publish_long.py            # Long-form publisher & scheduler
│   └── daily_runner.py            # Master runner yang dipanggil oleh cron
├── state/
│   ├── campaign_state.json        # Status pekan & hari aktif yang sedang berjalan
│   └── publish_history.json       # Log riwayat seluruh video yang telah tayang
├── requirements.txt
└── README.md
```

---

## 🚀 Menjalankan Uji Coba Lokal

```bash
# Install dependensi
pip install -r requirements.txt

# Uji coba render Short tanpa posting (Dry Run)
python scripts/daily_runner.py --day selasa --dry-run
```
