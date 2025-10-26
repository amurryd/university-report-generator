# file: create_sample_data.py
"""
Sample Data Creator
Creates multiple example CSV files for testing the report generator

Each category (students, finance) is split into multiple CSV files:
- data/students_semester_<n>.csv
- data/finance_<month>.csv

Run once:
    python create_sample_data.py
"""

import pandas as pd
from pathlib import Path
import random


def create_student_data():
    """Create separate sample student performance CSVs per semester"""
    print("Creating sample student data (per semester)...")

    first_names = ["Ahmad", "Budi", "Siti", "Dewi", "Eko", "Fitri", "Gita", "Hadi",
                   "Indah", "Joko", "Kartika", "Lina", "Made", "Nur", "Okta"]
    last_names = ["Santoso", "Pratama", "Wijaya", "Kusuma", "Putra", "Putri",
                  "Hidayat", "Rahman", "Sari", "Wati"]

    Path('data/students').mkdir(parents=True, exist_ok=True)

    semesters = range(1, 9)
    for semester in semesters:
        data = []
        for i in range(1, 16):  # 15 students per semester
            nama = f"{random.choice(first_names)} {random.choice(last_names)}"
            nim = f"21{semester:02d}{i:03d}"

            nilai_mid = random.randint(65, 95)
            nilai_uas = random.randint(60, 100)
            nilai_tugas = random.randint(70, 100)
            nilai_akhir = int(0.3 * nilai_mid + 0.4 * nilai_uas + 0.3 * nilai_tugas)

            if nilai_akhir >= 85:
                ipk = round(random.uniform(3.5, 4.0), 2)
            elif nilai_akhir >= 70:
                ipk = round(random.uniform(3.0, 3.5), 2)
            else:
                ipk = round(random.uniform(2.5, 3.0), 2)

            data.append({
                'NIM': nim,
                'Nama Mahasiswa': nama,
                'Semester': semester,
                'Nilai UTS': nilai_mid,
                'Nilai UAS': nilai_uas,
                'Nilai Tugas': nilai_tugas,
                'Nilai Akhir': nilai_akhir,
                'IPK': ipk,
                'Status': 'Aktif' if random.random() > 0.1 else 'Cuti'
            })

        df = pd.DataFrame(data)
        output_file = f"data/students/students_semester_{semester}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✓ Created: {output_file} ({len(df)} records)")


def create_finance_data():
    """Create separate sample finance CSVs per month"""
    print("\nCreating sample finance data (per month)...")

    categories = [
        'SPP (Uang Kuliah)',
        'Biaya Operasional',
        'Gaji Dosen & Staff',
        'Penelitian & Pengabdian',
        'Beasiswa Mahasiswa',
        'Pemeliharaan Gedung',
        'Peralatan & Laboratorium',
        'Dana Kegiatan Mahasiswa'
    ]

    months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni']

    Path('data/finance').mkdir(parents=True, exist_ok=True)

    for month in months:
        data = []
        for category in categories:
            if 'SPP' in category:
                pemasukan = random.randint(150_000_000, 200_000_000)
                pengeluaran = 0
            elif 'Gaji' in category:
                pemasukan = 0
                pengeluaran = random.randint(80_000_000, 120_000_000)
            elif 'Beasiswa' in category:
                pemasukan = random.randint(10_000_000, 20_000_000)
                pengeluaran = random.randint(15_000_000, 25_000_000)
            elif 'Penelitian' in category:
                pemasukan = random.randint(20_000_000, 40_000_000)
                pengeluaran = random.randint(15_000_000, 35_000_000)
            else:
                pemasukan = random.randint(0, 10_000_000)
                pengeluaran = random.randint(10_000_000, 50_000_000)

            data.append({
                'Bulan': month,
                'Kategori': category,
                'Pemasukan (Rp)': pemasukan,
                'Pengeluaran (Rp)': pengeluaran,
                'Saldo (Rp)': pemasukan - pengeluaran
            })

        df = pd.DataFrame(data)
        output_file = f"data/finance/finance_{month.lower()}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✓ Created: {output_file} ({len(df)} records)")


def create_akreditasi_data():
    """Create accreditation (akreditasi) metrics dataset"""
    print("\nCreating sample akreditasi data...")

    criteria = [
        "Visi Misi dan Tujuan",
        "Tata Pamong, Kepemimpinan, dan Kerjasama",
        "Mahasiswa",
        "Sumber Daya Manusia",
        "Keuangan, Sarana, dan Prasarana",
        "Pendidikan",
        "Penelitian",
        "Pengabdian Kepada Masyarakat",
        "Luaran dan Capaian Tridharma"
    ]

    Path('data/akreditasi').mkdir(parents=True, exist_ok=True)

    data = []
    for year in range(2018, 2025):
        for c in criteria:
            skor = round(random.uniform(2.5, 4.0), 2)
            data.append({
                "Tahun": year,
                "Kriteria": c,
                "Skor": skor,
                "Status": "Memadai" if skor >= 3.0 else "Perlu Peningkatan"
            })

    df = pd.DataFrame(data)
    output_file = "data/akreditasi/sample_akreditasi.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"✓ Created: {output_file} ({len(df)} records)")


def main():
    """Main function to create all sample data"""
    print("=" * 60)
    print("SAMPLE DATA CREATOR — MULTI FILE MODE")
    print("University AI Report Generator")
    print("=" * 60)
    print()

    try:
        create_student_data()
        create_finance_data()
        create_akreditasi_data()

        print("\n" + "=" * 60)
        print("✓ All sample CSV files created successfully!")
        print("=" * 60)
        print("Check your 'data' folder for:")
        print("- students/students_semester_<n>.csv")
        print("- finance/finance_<month>.csv")
        print("- akreditasi/sample_akreditasi.csv")
        print()

    except Exception as e:
        print(f"\n❌ Error creating sample data: {e}")
        print("Make sure you have pandas installed:")
        print("  pip install pandas")


if __name__ == "__main__":
    main()
