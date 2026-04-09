import os
from django.conf import settings
from pricing.models import Region


def generate_excel_report(report_id, market_name, segments_data, plan_type="basic",
                          selected_countries=None, is_demo=True,
                          base_year=2024, forecast_year=2033,
                          metric="Revenue", currency="USD"):
    """
    Generate XML Spreadsheet 2003 (.xls) report with professional styling.
    
    Structure:
    - Home: Overview, report info, segmentation summary
    - Global: Revenue/Volume tables with region breakdown + segment tables
    - Region sheets: Revenue/Volume with country breakdown + segment tables
    - Country sheets: Revenue/Volume + segment breakdown tables
    
    All demo values use xx.xx / x.x% placeholders.
    All content is 100% dynamic based on filters.
    """
    if not selected_countries:
        selected_countries = ["Global"]

    years = list(range(int(base_year), int(forecast_year) + 1))
    num_years = len(years)

    curr_map = {"USD": "USD Million", "EUR": "EUR Million", "GBP": "GBP Million", "JPY": "JPY Billion"}
    curr_label = curr_map.get(currency, "USD Million")
    vol_label = "Units/Tons"

    SOURCE_TEXT = "Source: Primary Interviews, Secondary Research, Internal Databases and Forecastly.io Research"

    # Normalize metric
    metric_lower = str(metric).lower()
    do_rev = 'revenue' in metric_lower or 'both' in metric_lower
    do_vol = 'volume' in metric_lower or 'both' in metric_lower
    if not do_rev and not do_vol:
        do_rev = True

    # Resolve regions & countries
    all_regions = Region.objects.prefetch_related('countries')
    country_to_region = {}
    region_countries_map = {}

    for region in all_regions:
        for c in region.countries.all():
            country_to_region[c.name] = region.name
            if region.name not in region_countries_map:
                region_countries_map[region.name] = []
            region_countries_map[region.name].append(c.name)

    selected_c_names = [c for c in selected_countries if c != "Global"]
    has_global = "Global" in selected_countries

    # Determine active regions from selected countries
    active_regions = []
    seen_regions = set()
    for c in selected_c_names:
        rg = country_to_region.get(c)
        if rg and rg not in seen_regions:
            active_regions.append(rg)
            seen_regions.add(rg)

    # Extract segments
    segments = segments_data.get('segments', [])

    # ═══════════════════════════════════════════════
    # XML HELPERS
    # ═══════════════════════════════════════════════
    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    def make_cell(val, style_id, col_type="String"):
        return '<Cell ss:StyleID="%s"><Data ss:Type="%s">%s</Data></Cell>' % (style_id, col_type, esc(val))

    def make_merge(val, style_id, merge_across, col_type="String"):
        return '<Cell ss:StyleID="%s" ss:MergeAcross="%d"><Data ss:Type="%s">%s</Data></Cell>' % (style_id, merge_across, col_type, esc(val))

    # ═══════════════════════════════════════════════
    # TABLE GENERATOR
    # ═══════════════════════════════════════════════
    def make_table(title, first_col_label, items, add_total=True):
        """Generate a revenue/volume data table with xx.xx values."""
        nc = num_years + 1  # merge across = (years + CAGR) count - 1
        rows = []

        # Title banner
        rows.append('<Row ss:Height="30">%s</Row>' % make_merge(title, 'title', nc))

        # Header row
        hdr = '<Row ss:Height="24">'
        hdr += make_cell(first_col_label, 'hdr')
        for y in years:
            hdr += make_cell(str(y), 'hdrC')
        hdr += make_cell("CAGR (%d-%d)" % (years[0], years[-1]), 'hdrC')
        hdr += '</Row>'
        rows.append(hdr)

        # Data rows
        for item in items:
            dr = '<Row>'
            dr += make_cell(item, 'label')
            for _ in years:
                dr += make_cell('xx.xx', 'data')
            dr += make_cell('x.x%', 'data')
            dr += '</Row>'
            rows.append(dr)

        # Total row
        if add_total and len(items) > 1:
            tr = '<Row ss:Height="24">'
            tr += make_cell('Total', 'totalL')
            for _ in years:
                tr += make_cell('xx.xx', 'totalC')
            tr += make_cell('x.x%', 'totalC')
            tr += '</Row>'
            rows.append(tr)

        # Source row
        rows.append('<Row>%s</Row>' % make_merge(SOURCE_TEXT, 'src', nc))

        return '\n'.join(rows)

    def make_rev_line(prefix):
        """Single revenue line (no sub-items)."""
        nc = num_years + 1
        rows = []
        rows.append('<Row ss:Height="30">%s</Row>' % make_merge(prefix + " (" + curr_label + ")", 'title', nc))
        hdr = '<Row ss:Height="24">'
        hdr += make_cell('', 'hdr')
        for y in years:
            hdr += make_cell(str(y), 'hdrC')
        hdr += make_cell("CAGR (%d-%d)" % (years[0], years[-1]), 'hdrC')
        hdr += '</Row>'
        rows.append(hdr)
        dr = '<Row>'
        dr += make_cell("Revenue (" + curr_label + ")", 'label')
        for _ in years:
            dr += make_cell('xx.xx', 'data')
        dr += make_cell('x.x%', 'data')
        dr += '</Row>'
        rows.append(dr)
        rows.append('<Row>%s</Row>' % make_merge(SOURCE_TEXT, 'src', nc))
        return '\n'.join(rows)

    def make_vol_line(prefix):
        """Single volume line (no sub-items)."""
        nc = num_years + 1
        rows = []
        rows.append('<Row ss:Height="30">%s</Row>' % make_merge(prefix + " (" + vol_label + ")", 'title', nc))
        hdr = '<Row ss:Height="24">'
        hdr += make_cell('', 'hdr')
        for y in years:
            hdr += make_cell(str(y), 'hdrC')
        hdr += make_cell("CAGR (%d-%d)" % (years[0], years[-1]), 'hdrC')
        hdr += '</Row>'
        rows.append(hdr)
        dr = '<Row>'
        dr += make_cell("Volume (" + vol_label + ")", 'label')
        for _ in years:
            dr += make_cell('xx.xx', 'data')
        dr += make_cell('x.x%', 'data')
        dr += '</Row>'
        rows.append(dr)
        rows.append('<Row>%s</Row>' % make_merge(SOURCE_TEXT, 'src', nc))
        return '\n'.join(rows)

    # ═══════════════════════════════════════════════
    # COLUMN CONFIG
    # ═══════════════════════════════════════════════
    def col_config():
        # Clean table: no hidden/blank index columns
        cols = '<Column ss:Width="250"/>\n'
        for _ in range(num_years + 1):  # years + CAGR
            cols += '<Column ss:Width="90"/>\n'
        return cols

    # ═══════════════════════════════════════════════
    # STYLES (matching reference file exactly)
    # ═══════════════════════════════════════════════
    STYLES = '''<Styles>
 <Style ss:ID="Default"><Font ss:FontName="Calibri" ss:Size="10"/></Style>
 <Style ss:ID="title">
  <Font ss:FontName="Calibri" ss:Size="11" ss:Bold="1" ss:Color="#FFFFFF"/>
  <Interior ss:Color="#0A3D62" ss:Pattern="Solid"/>
  <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
  <Borders>
   <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#0A3D62"/>
   <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#0A3D62"/>
   <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#0A3D62"/>
   <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#0A3D62"/>
  </Borders>
 </Style>
 <Style ss:ID="hdr">
  <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#0A3D62"/>
  <Interior ss:Color="#AADDE9" ss:Pattern="Solid"/>
  <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
  <Borders>
   <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
  </Borders>
 </Style>
 <Style ss:ID="hdrC">
  <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#0A3D62"/>
  <Interior ss:Color="#AADDE9" ss:Pattern="Solid"/>
  <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
  <Borders>
   <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
  </Borders>
 </Style>
 <Style ss:ID="label">
  <Font ss:FontName="Calibri" ss:Size="10" ss:Color="#0A3D62"/>
  <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
  <Borders>
   <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
  </Borders>
 </Style>
 <Style ss:ID="data">
  <Font ss:FontName="Calibri" ss:Size="10" ss:Color="#37474F"/>
  <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
  <Borders>
   <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
  </Borders>
 </Style>
 <Style ss:ID="totalL">
  <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#0A3D62"/>
  <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
  <Borders>
   <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="2" ss:Color="#0A3D62"/>
   <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="2" ss:Color="#0A3D62"/>
   <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#0A3D62"/>
   <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#0A3D62"/>
  </Borders>
 </Style>
 <Style ss:ID="totalC">
  <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#0A3D62"/>
  <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
  <Borders>
   <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="2" ss:Color="#0A3D62"/>
   <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="2" ss:Color="#0A3D62"/>
   <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#0A3D62"/>
   <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#0A3D62"/>
  </Borders>
 </Style>
 <Style ss:ID="src">
  <Font ss:FontName="Calibri" ss:Size="8" ss:Italic="1" ss:Color="#90A4AE"/>
  <Alignment ss:Horizontal="Left" ss:Vertical="Center"/>
 </Style>
 <Style ss:ID="homeTitle">
  <Font ss:FontName="Calibri" ss:Size="20" ss:Bold="1" ss:Color="#0A3D62"/>
 </Style>
 <Style ss:ID="homeBrand">
  <Font ss:FontName="Calibri" ss:Size="12" ss:Bold="1" ss:Color="#42A5F5"/>
 </Style>
 <Style ss:ID="homeInfo">
  <Font ss:FontName="Calibri" ss:Size="11" ss:Bold="1" ss:Color="#0A3D62"/>
 </Style>
 <Style ss:ID="homeText">
  <Font ss:FontName="Calibri" ss:Size="11" ss:Color="#333333"/>
 </Style>
 <Style ss:ID="warn">
  <Font ss:FontName="Calibri" ss:Size="11" ss:Bold="1" ss:Color="#D84315"/>
  <Interior ss:Color="#FFF3E0" ss:Pattern="Solid"/>
  <Borders>
   <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Top" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Left" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
   <Border ss:Position="Right" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#78909C"/>
  </Borders>
 </Style>
 <Style ss:ID="demo">
  <Font ss:FontName="Calibri" ss:Size="9" ss:Italic="1" ss:Color="#AAAAAA"/>
 </Style>
 <Style ss:ID="segHead">
  <Font ss:FontName="Calibri" ss:Size="10" ss:Bold="1" ss:Color="#0A3D62"/>
 </Style>
 <Style ss:ID="segSub">
  <Font ss:FontName="Calibri" ss:Size="9" ss:Color="#475569"/>
 </Style>
</Styles>'''

    # ═══════════════════════════════════════════════
    # BUILD HOME SHEET
    # ═══════════════════════════════════════════════
    def build_home_sheet():
        rows = []
        rows.append('<Row>%s</Row>' % make_cell('Forecastly.io', 'homeBrand'))
        rows.append('<Row>%s</Row>' % make_cell(market_name, 'homeTitle'))

        report_type = "Demo Report" if is_demo else "Full Report"
        rows.append('<Row>%s</Row>' % make_cell("Forecastly.io " + report_type, 'homeInfo'))

        plan_labels = {"basic": "Basic", "professional": "Professional", "enterprise": "Enterprise"}
        c_count = len(selected_c_names)

        info_items = [
            ("Report ID", report_id),
            ("Plan", plan_labels.get(plan_type, plan_type.title())),
            ("Global", "Yes" if has_global else "No"),
            ("Countries", str(c_count)),
            ("Segmentation", "Yes" if plan_type == 'enterprise' else "No"),
            ("Forecast", "%s-%s" % (base_year, forecast_year)),
            ("Metric", metric),
            ("Currency", curr_label),
        ]
        for label, val in info_items:
            rows.append('<Row>%s</Row>' % make_cell("%s: %s" % (label, val), 'homeText'))

        if is_demo:
            rows.append('<Row>%s</Row>' % make_cell(
                "DEMO REPORT - Placeholder data (xx.xx). Real data available after purchase.", 'warn'))
            rows.append('<Row>%s</Row>' % make_cell(
                "This demo shows the exact structure, sheets, and segmentation of the paid report.", 'demo'))

        rows.append('<Row>%s</Row>' % make_cell("Market Segmentation Overview", 'homeInfo'))

        for seg in segments:
            seg_name = seg.get('name', '')
            subs = seg.get('subsegments', seg.get('items', []))
            rows.append('<Row>%s</Row>' % make_cell("  %s" % seg_name, 'segHead'))
            if plan_type != 'basic':
                for sub in subs:
                    rows.append('<Row>%s</Row>' % make_cell("    - %s" % sub, 'segSub'))

        # Explicitly append Geographic segmentation for clarity 
        rows.append('<Row>%s</Row>' % make_cell("  By Geography", 'segHead'))
        rows.append('<Row>%s</Row>' % make_cell("    - By Region", 'segSub'))
        rows.append('<Row>%s</Row>' % make_cell("    - By Country", 'segSub'))

        return '''<Worksheet ss:Name="Home">
<Table>
<Column ss:Width="500"/>
%s
</Table>
</Worksheet>''' % '\n'.join(rows)

    # ═══════════════════════════════════════════════
    # BUILD DATA SHEET (for Global / Region / Country)
    # ═══════════════════════════════════════════════
    def build_data_sheet(sheet_name, geo_label, breakdown_label=None, breakdown_items=None,
                         include_segments=False):
        """
        Build a complete data sheet with:
        - Revenue line for this geo
        - Revenue breakdown by items (if provided)
        - Revenue segment tables (if enterprise)
        - Volume line + breakdown + segments (if do_vol)
        """
        all_rows = []

        # === REVENUE SECTION ===
        if do_rev:
            # Main revenue line
            all_rows.append(make_rev_line(
                "%s %s, %s-%s" % (geo_label, market_name, base_year, forecast_year)))

            # Breakdown by sub-items (regions or countries)
            if breakdown_items and len(breakdown_items) > 0:
                all_rows.append(make_table(
                    "%s %s, by %s (%s)" % (geo_label, market_name, breakdown_label, curr_label),
                    breakdown_label, breakdown_items))

            # Segment tables (Enterprise only)
            if include_segments:
                for seg in segments:
                    seg_name = seg.get('name', 'Segment')
                    subs = seg.get('subsegments', seg.get('items', []))
                    all_rows.append(make_table(
                        "%s %s, by %s (%s)" % (geo_label, market_name, seg_name, curr_label),
                        seg_name, subs))

        # === VOLUME SECTION ===
        if do_vol:
            # Main volume line
            all_rows.append(make_vol_line(
                "%s %s, %s-%s" % (geo_label, market_name, base_year, forecast_year)))

            # Breakdown by sub-items
            if breakdown_items and len(breakdown_items) > 0:
                all_rows.append(make_table(
                    "%s %s, by %s (%s)" % (geo_label, market_name, breakdown_label, vol_label),
                    breakdown_label, breakdown_items))

            # Segment tables (Enterprise only)
            if include_segments:
                for seg in segments:
                    seg_name = seg.get('name', 'Segment')
                    subs = seg.get('subsegments', seg.get('items', []))
                    all_rows.append(make_table(
                        "%s %s, by %s (%s)" % (geo_label, market_name, seg_name, vol_label),
                        seg_name, subs))

        safe_name = sheet_name[:31].replace('/', '-').replace('\\', '-').replace('[', '(').replace(']', ')')

        return '''<Worksheet ss:Name="%s">
<Table>
%s
%s
</Table>
</Worksheet>''' % (esc(safe_name), col_config(), '\n'.join(all_rows))

    # ═══════════════════════════════════════════════
    # ASSEMBLE ALL SHEETS
    # ═══════════════════════════════════════════════
    sheets = []

    # 1. Home sheet (all plans)
    sheets.append(build_home_sheet())

    # Skip data sheets for basic plan
    if plan_type == 'basic':
        pass

    elif plan_type == 'professional':
        # Global sheet
        if has_global:
            sheets.append(build_data_sheet(
                "Global", "Global",
                breakdown_label="Region",
                breakdown_items=active_regions if active_regions else None,
                include_segments=False
            ))

        # Regional sheets
        for region_name in active_regions:
            r_countries = [c for c in selected_c_names if country_to_region.get(c) == region_name]
            sheets.append(build_data_sheet(
                region_name, region_name,
                breakdown_label="Country",
                breakdown_items=r_countries if r_countries else None,
                include_segments=False
            ))

            # Country sheets
            for country_name in r_countries:
                sheets.append(build_data_sheet(
                    country_name, country_name,
                    include_segments=False
                ))

    elif plan_type == 'enterprise':
        # Global sheet with full segmentation
        if has_global:
            sheets.append(build_data_sheet(
                "Global", "Global",
                breakdown_label="Region",
                breakdown_items=active_regions if active_regions else None,
                include_segments=True
            ))

        # Regional sheets with segmentation
        for region_name in active_regions:
            r_countries = [c for c in selected_c_names if country_to_region.get(c) == region_name]
            sheets.append(build_data_sheet(
                region_name, region_name,
                breakdown_label="Country",
                breakdown_items=r_countries if r_countries else None,
                include_segments=True
            ))

            # Country sheets with full segment breakdown
            for country_name in r_countries:
                sheets.append(build_data_sheet(
                    country_name, country_name,
                    include_segments=True
                ))

    # ═══════════════════════════════════════════════
    # BUILD FINAL XML
    # ═══════════════════════════════════════════════
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
%s
%s
</Workbook>''' % (STYLES, '\n'.join(sheets))

    # Save as .xls (XML Spreadsheet 2003 format)
    filename = "%s_%s.xls" % (report_id, plan_type)
    media_root = os.path.join(settings.BASE_DIR, 'media', 'reports')
    os.makedirs(media_root, exist_ok=True)
    filepath = os.path.join(media_root, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(xml)

    return "reports/%s" % filename
