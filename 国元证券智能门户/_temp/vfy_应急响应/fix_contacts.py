# -*- coding: utf-8 -*-
"""修正应急响应联系人"""

path = r'C:\Users\11039\WorkBuddy\国元证券智能门户\_temp\应急修正\word\document.xml'
with open(path, 'r', encoding='utf-8') as f:
    xml = f.read()

# The 联系人表 has 7 rows: 应急总指挥, 技术负责人, 系统管理员, 数据库管理员, 网络安全管理员, 应用负责人, 业务联系人
# The 系统设备表 also has [待填写] entries for IPs and configs
# We need to find and replace the NAME cells in the 联系人表

# Find the 联系人 table section - search for "岗  位" header
idx_start = xml.find('岗\u3000\u3000位')
if idx_start == -1:
    idx_start = xml.find('岗  位')

# Find all [待填写] entries
import re
count = 0
replacements = []

# Sequential replacement: first 7 [待填写] are the 联系人 names
# Map roles to names:
contact_names = {
    0: '何金钟',    # 应急总指挥
    1: '[待填写]',   # 技术负责人
    2: '[待填写]',   # 系统管理员
    3: '[待填写]',   # 数据库管理员
    4: '[待填写]',   # 网络安全管理员
    5: '程文斐',    # 应用负责人
    6: '葛鹏飞',    # 业务联系人
}

# Find all [待填写] positions
positions = []
pos = 0
while True:
    pos = xml.find('[待填写]', pos)
    if pos == -1:
        break
    positions.append(pos)
    pos += 1

print(f'Found {len(positions)} [待填写] entries total')

# Find which ones are in the 联系人表
# Look at context around each position to determine if it's in the contacts table
contact_count = 0
for i, pos in enumerate(positions):
    # Check context 100 chars before
    context_before = xml[max(0,pos-100):pos]
    # If this looks like a name cell (between role and responsibility in the 联系人 table)
    # Just use sequential order - first 7 are contacts
    if i < 7:
        role = list(contact_names.keys())[i]
        name = contact_names[role]
        if name and name != '[待填写]':
            old = '[待填写]'
            new = name
            # Only replace the first occurrence (sequential)
            xml = xml.replace('[待填写]', new, 1)
            print(f'  #{i}: contact row -> {new}')
            contact_count += 1

print(f'Updated {contact_count} contact names')
print()

# Verify
for name in ['何金钟', '程文斐', '葛鹏飞']:
    cnt = xml.count(name)
    print(f'{name}: {cnt}')

with open(path, 'w', encoding='utf-8') as f:
    f.write(xml)
print('\nDone')
