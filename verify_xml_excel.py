import xml.etree.ElementTree as ET

file_path = "c:\\Users\\Santosh\\Desktop\\market\\REP-35941_professional.xls"

# Remove namespaces for easier querying
def strip_ns(tag):
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

try:
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    print("=== READING EXCEL XML ===")
    
    for worksheet in root.findall('.//{*}Worksheet'):
        ws_name = worksheet.attrib.get('{urn:schemas-microsoft-com:office:spreadsheet}Name', 'Unknown')
        print(f"\n--- SHEET: {ws_name} ---")
        
        table = worksheet.find('.//{*}Table')
        if table is not None:
            rows = table.findall('.//{*}Row')
            print(f"Total Rows: {len(rows)}")
            
            # Print first 15 rows to check structure and data
            for i, row in enumerate(rows[:15]):
                cells = row.findall('.//{*}Cell')
                row_data = []
                for cell in cells:
                    data = cell.find('.//{*}Data')
                    if data is not None and data.text:
                        row_data.append(data.text)
                    else:
                        row_data.append("")
                print(f"Row {i+1}: {row_data}")
except Exception as e:
    print(f"Error parsing xml excel: {e}")
