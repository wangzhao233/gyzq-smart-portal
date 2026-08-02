import re, xml.etree.ElementTree as ET

path = r'C:\Users\11039\WorkBuddy\国元证券智能门户\_temp\应急最终\word\document.xml'

# Read and validate original
with open(path, 'r', encoding='utf-8') as f:
    xml = f.read()

try:
    ET.fromstring(xml)
    print('✅ Original XML is valid')
except ET.ParseError as e:
    print(f'⚠️ Original XML error: line {e.position[0]}')

# ===========================
# Fix 1: RTO表第3行补服务名
# ===========================
# Find the RTO table - search for table containing both "RTO（分钟）" and "服务名称"
for m in re.finditer(r'<w:tbl', xml):
    tbl_start = m.start()
    tbl_end = xml.find('</w:tbl>', tbl_start) + 8
    tbl = xml[tbl_start:tbl_end]
    if 'RTO' in tbl and '服务名称' in tbl:
        rows = list(re.finditer(r'<w:tr[ >].*?</w:tr>', tbl, re.DOTALL))
        
        # Find rows
        # Row 0: header (服务名称 | RTO | RPO)
        # Row 1: Nginx (前端接入服务（Nginx）| 15 | 0) 
        # Row 2+: scattered data
        
        if len(rows) >= 8:  # Still has scattered rows
            # Get template cells from Row 1 (Nginx row)
            row1_cells = re.findall(r'<w:tc>.*?</w:tc>', rows[1].group(0), re.DOTALL)
            if len(row1_cells) >= 3:
                # Build row 2: 元信后端服务集群 | 15 | 15
                c1 = row1_cells[0].replace('前端接入服务（Nginx）', '元信后端服务集群')
                row2 = '<w:tr>' + c1 + row1_cells[1] + row1_cells[2].replace('0', '15') + '</w:tr>'
                
                # Build row 3: 消息推送服务 | 10 | 15
                d1 = row1_cells[0].replace('前端接入服务（Nginx）', '消息推送服务')
                d2 = row1_cells[1].replace('15', '10')
                d3 = row1_cells[2].replace('0', '15')
                row3 = '<w:tr>' + d1 + d2 + d3 + '</w:tr>'
                
                # Location: after row1 end
                row1_abs_end = tbl_start + rows[1].start() + len(rows[1].group(0))
                row1_abs_end = row1_abs_end - len('</w:tr>') + rows[1].group(0).rfind('</w:tr>') + 6
                
                # Calculate properly
                row1_end_in_tbl = rows[1].start() + rows[1].group(0).rfind('</w:tr>') + 6
                row1_abs_end = tbl_start + row1_end_in_tbl
                
                # Last row end
                last_row_end_in_tbl = rows[-1].start() + rows[-1].group(0).rfind('</w:tr>') + 6
                last_row_abs_end = tbl_start + last_row_end_in_tbl
                
                old_content = xml[row1_abs_end:last_row_abs_end]
                new_content = row2 + row3
                
                xml = xml[:row1_abs_end] + new_content + xml[last_row_abs_end:]
                print(f'✅ Fix 1: RTO表重建 ({len(old_content)} -> {len(new_content)} chars)')
                break

# ===========================
# Fix 2: 系统影响范围恢复顺序
# ===========================
step1 = '1) 网络连通性（Nginx/网关）'
step7 = '7) 前端Web服务'

idx1 = xml.find(step1)
idx7 = xml.find(step7)

if idx1 > 0 and idx7 > 0:
    # Find paragraph boundaries
    p1_end = xml.find('</w:p>', idx1) + 6
    p7_start = xml.rfind('<w:p', 0, idx7)
    p7_end = xml.find('</w:p>', idx7) + 6
    
    # Get step7 template
    step7_para = xml[p7_start:p7_end]
    
    # Find 4.3 boundary  
    idx43 = xml.find('4.3 数据影响范围', idx7)
    if idx43 > 0:
        p43_start = xml.rfind('<w:p', 0, xml.find('4.3', idx7))
        
        # Delete existing content between step1 and 4.3
        between = xml[p1_end:p43_start]
        xml = xml[:p1_end] + xml[p43_start:]
        
        # Insert new steps
        steps = ['2) 安全网关服务', '3) 元信后端服务集群', '4) 数据库服务',
                 '5) 缓存服务', '6) 消息推送服务', '7) 前端Web服务']
        
        new_content = ''
        for s in steps:
            new_para = step7_para.replace('7) 前端Web服务', s)
            new_content += new_para
        
        xml = xml[:p1_end] + new_content + xml[p1_end:]
        print(f'✅ Fix 2: 恢复顺序补充 ({len(steps)}步)')

# ===========================
# Fix 3: 场景四/五正文标题加style=25
# ===========================  
# Find the 2nd occurrence (first body, not TOC)
for scene in ['场景四：元信后端服务异常', '场景五：数据库服务异常']:
    # Find all occurrences
    positions = []
    search = 0
    while True:
        idx = xml.find(scene, search)
        if idx < 0:
            break
        # Check style
        para_start = xml.rfind('<w:p', 0, idx)
        para = xml[para_start:para_start+300]
        style_m = re.search(r'<w:pStyle w:val=\"(\d+)\"/>', para)
        style = style_m.group(1) if style_m else '无样式'
        positions.append((idx, style))
        search = idx + 1
    
    # The 2nd occurrence is the body one (not TOC)
    if len(positions) >= 2:
        idx = positions[1][0]
        para_start = xml.rfind('<w:p', 0, idx)
        para_end = xml.find('</w:p>', idx)
        
        # Check if pPr already has style
        ppr = xml[para_start:para_end]
        if '<w:pStyle' not in ppr:
            # Need to add pStyle to pPr
            ppr_tag = re.search(r'<w:pPr>', ppr)
            if ppr_tag:
                after_ppr = para_start + ppr_tag.end()
                xml = xml[:after_ppr] + '<w:pStyle w:val="25"/>' + xml[after_ppr:]
                print(f'✅ Fix 3: {scene[:6]}... + style=25')

# ===========================
# Validate and save
# ===========================
try:
    ET.fromstring(xml)
    print('✅ Final XML is valid')
except ET.ParseError as e:
    print(f'⚠️ Final XML error: line {e.position[0]}, col {e.position[1]}')
    lines = xml.split('\n')
    if e.position[0] <= len(lines):
        print(f'  Line: {lines[e.position[0]-1][:150]}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(xml)
