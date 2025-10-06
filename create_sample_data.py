"""
Sample Data Creator
Creates example Excel files for testing the report generator

Run this script once to create sample data files:
python create_sample_data.py
"""

import pandas as pd
from pathlib import Path
import random

def create_student_data():
    """Create sample student performance data"""
    print("Creating sample student data...")
    
    # Indonesian names for realistic demo
    first_names = ["Ahmad", "Budi", "Siti", "Dewi", "Eko", "Fitri", "Gita", "Hadi", 
                   "Indah", "Joko", "Kartika", "Lina", "Made", "Nur", "Okta"]
    last_names = ["Santoso", "Pratama", "Wijaya", "Kusuma", "Putra", "Putri", 
                  "Hidayat", "Rahman", "Sari", "Wati"]
    
    # Generate 30 student records
    data = []
    for i in range(1, 31):
        nama = f"{random.choice(first_names)} {random.choice(last_names)}"
        nim = f"210{i:04d}"
        
        # Generate realistic grades
        nilai_mid = random.randint(65, 95)
        nilai_uas = random.randint(60, 100)
        nilai_tugas = random.randint(70, 100)
        nilai_akhir = int(0.3 * nilai_mid + 0.4 * nilai_uas + 0.3 * nilai_tugas)
        
        # Calculate GPA (IPK) based on final grade
        if nilai_akhir >= 85:
            ipk = round(random.uniform(3.5, 4.0), 2)
        elif nilai_akhir >= 70:
            ipk = round(random.uniform(3.0, 3.5), 2)
        else:
            ipk = round(random.uniform(2.5, 3.0), 2)
        
        semester = random.choice([4, 5, 6])
        
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
    
    # Create DataFrame and save
    df = pd.DataFrame(data)
    
    # Ensure data directory exists
    Path('data').mkdir(exist_ok=True)
    
    # Save to Excel
    output_file = 'data/sample_students.xlsx'
    df.to_excel(output_file, index=False)
    print(f"✓ Created: {output_file}")
    print(f"  - {len(df)} student records")
    print(f"  - Columns: {', '.join(df.columns)}\n")

def create_finance_data():
    """Create sample financial data"""
    print("Creating sample finance data...")
    
    # Define categories and months
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
    
    data = []
    for month in months:
        for category in categories:
            # Generate realistic financial figures (in Rupiah)
            if 'SPP' in category:
                pemasukan = random.randint(150_000_000, 200_000_000)
                pengeluaran = 0
            elif 'Gaji' in category:
                pemasukan = 0
                pengeluaran = random.randint(80_000_000, 120_000_000)
            elif 'Beasiswa' in category:
                pemasukan = random.randint(10_000_000, 20_000_000)  # Dana dari sponsor
                pengeluaran = random.randint(15_000_000, 25_000_000)
            elif 'Penelitian' in category:
                pemasukan = random.randint(20_000_000, 40_000_000)  # Grant
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
    
    # Create DataFrame and save
    df = pd.DataFrame(data)
    
    # Ensure data directory exists
    Path('data').mkdir(exist_ok=True)
    
    # Save to Excel
    output_file = 'data/sample_finance.xlsx'
    df.to_excel(output_file, index=False)
    print(f"✓ Created: {output_file}")
    print(f"  - {len(df)} financial records")
    print(f"  - Columns: {', '.join(df.columns)}\n")

def main():
    """Main function to create all sample data"""
    print("=" * 60)
    print("SAMPLE DATA CREATOR")
    print("University AI Report Generator")
    print("=" * 60)
    print()
    
    try:
        create_student_data()
        create_finance_data()
        
        print("=" * 60)
        print("✓ All sample data files created successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Check the 'data' folder for the Excel files")
        print("2. You can open them in Excel to see the data")
        print("3. Run the main application: python main.py")
        print("4. Choose option 3 (Demo) to process these files")
        print()
        
    except Exception as e:
        print(f"\n❌ Error creating sample data: {str(e)}")
        print("Make sure you have pandas and openpyxl installed:")
        print("  pip install pandas openpyxl")

if __name__ == "__main__":
    main()