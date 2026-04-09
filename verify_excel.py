import pandas as pd

file_path = "c:\\Users\\Santosh\\Desktop\\market\\REP-35941_professional.xls"

try:
    xls = pd.ExcelFile(file_path)
    print("Sheets:", xls.sheet_names)
    
    # Read Global sheet
    if 'Global' in xls.sheet_names:
        df_global = pd.read_excel(xls, 'Global')
        print("\n--- GLOBAL SHEET (First 20 rows) ---")
        print(df_global.head(20).to_string())
        
    # Read a country sheet
    country_sheets = [s for s in xls.sheet_names if s not in ['Home', 'Global', 'North America', 'Europe', 'Asia-Pacific', 'Latin America', 'MEA']]
    if country_sheets:
        first_country = country_sheets[0]
        df_country = pd.read_excel(xls, first_country)
        print(f"\n--- {first_country.upper()} SHEET (First 20 rows) ---")
        print(df_country.head(20).to_string())
        
except Exception as e:
    print(f"Error reading excel: {e}")
