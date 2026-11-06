# UAP Access Control CTF — Secure File Manager

Website CTF satu challenge AppArmor untuk Ujian Akhir Praktikum Modul 6. UI, API, dan pemeriksaan sintaks berjalan di dalam Docker container. Profil kiriman tidak pernah dimuat ke kernel.

## Persiapan
- Docker Engine atau Docker Desktop dengan Linux containers.
- Docker Compose plugin.
- Salinan repository project.

## Konfigurasi flag
Salin .env.example menjadi .env, lalu ganti nilai CTF_FLAG dengan flag rahasia untuk praktikan. Jangan commit file .env atau membagikan nilai flag melalui frontend.

## Build dan jalankan
Perintah utama deployment:
    docker compose up -d --build

Buka http://localhost:8000. Port host dapat diubah melalui CTF_PORT pada file .env.

Untuk praktikan di jaringan yang sama, berikan alamat IP server Docker dan port yang dipublikasikan, misalnya http://192.0.2.10:8000. Batasi akses menggunakan firewall atau jaringan praktikum; jangan mengekspos website ke internet publik tanpa proteksi.

## Status dan log
    docker compose ps
    docker compose logs -f

## Menjalankan test di image/container
    docker compose run --rm --no-deps app python3 -m unittest discover -s tests -v

Test parser menjalankan apparmor_parser -Q -K --abort-on-error di dalam image. Test menguji variasi rule sementara rw dan wr melalui API serta parser resmi.

## Menghentikan aplikasi
    docker compose down

## Keamanan dan batas validasi
- Proses di dalam container berjalan sebagai user non-root, filesystem root read-only, tanpa Linux capabilities, dan tanpa privilege tambahan. /tmp tersedia sebagai tmpfs khusus untuk berkas parser.
- Container tidak memiliki mount Docker socket, mount policy host, atau akses untuk memuat policy ke kernel.
- Parser resmi hanya memeriksa sintaks dalam mode -Q -K. Hasilnya tidak mengklaim profil telah dimuat, enforced, atau diuji terhadap akses kernel aktual.
- Pemeriksaan semantik memeriksa rule challenge dalam profil target; ini bukan simulator penuh seluruh keputusan akses AppArmor.
- Tidak ada code atau executable peserta yang dijalankan.

Deployment normal dan validasi praktikan dilakukan melalui Docker Compose. Host hanya memerlukan Docker Engine dan Docker Compose; Python dan AppArmor parser dipasang di image, bukan di host.
