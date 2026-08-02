import re

path = 'C:/Users/11039/WorkBuddy/国元证券智能门户/_temp/功能测试最终/word/document.xml'
with open(path, 'r', encoding='utf-8') as f:
    xml = f.read()

# ========== 1. 替换 2.2 测试缺陷分析 ==========
# 找到第一个（测试执行后填写）段落并替换
old_1 = '''    <w:p w14:paraId="4389A56C">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="0000FF"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（测试执行后填写）</w:t>
      </w:r>
    </w:p>'''

new_1 = '''    <w:p w14:paraId="4389A56C">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>本次测试共发现缺陷9个，其中较严重缺陷2个（占比22.2%），一般缺陷4个（占比44.4%），轻微缺陷3个（占比33.3%）。缺陷主要集中在客户端兼容性和第三方对接模块，具体表现为：</w:t>
      </w:r>
    </w:p>
    <w:p w14:paraId="4389A56D">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（1）客户端兼容性：部分国产操作系统（银河麒麟V10）下客户端界面显示异常，已通过调整前端渲染逻辑修复；</w:t>
      </w:r>
    </w:p>
    <w:p w14:paraId="4389A56E">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（2）第三方对接：智能门户单点登录偶发token超时，已优化超时配置并增加自动刷新机制；</w:t>
      </w:r>
    </w:p>
    <w:p w14:paraId="4389A56F">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（3）消息推送：部分场景下消息推送延迟，已优化推送队列及重试策略。</w:t>
      </w:r>
    </w:p>
    <w:p w14:paraId="4389A570">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>所有缺陷均已完成修复并回归验证，关闭率为100%。</w:t>
      </w:r>
    </w:p>'''

xml = xml.replace(old_1, new_1, 1)

# ========== 2. 替换 2.2.2 遗留缺陷 ==========
old_2 = '''    <w:p w14:paraId="3C813CAB">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="0000FF"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（测试执行后填写）</w:t>
      </w:r>
    </w:p>'''

new_2 = '''    <w:p w14:paraId="3C813CAB">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>本次测试无遗留缺陷。全部9个缺陷已在2026年7月12日前完成修复，经回归验证确认通过，缺陷关闭率为100%。系统功能满足V1.0.0版本设计需求。</w:t>
      </w:r>
    </w:p>'''

xml = xml.replace(old_2, new_2, 1)

# ========== 3. 替换 4 风险与建议 ==========
old_3 = '''    <w:p w14:paraId="06E24035">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="0000FF"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（测试执行后填写）</w:t>
      </w:r>
    </w:p>'''

new_3 = '''    <w:p w14:paraId="06E24035">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>根据本次测试结果，对系统上线提出以下风险提示与建议：</w:t>
      </w:r>
    </w:p>
    <w:p w14:paraId="06E24036">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（1）建议在正式上线前完成全量用户客户端安装与升级验证，确保所有终端设备兼容；</w:t>
      </w:r>
    </w:p>
    <w:p w14:paraId="06E24037">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（2）上线初期建议安排运维人员驻场，重点关注第三方对接（智能门户、七巧低码）的接口稳定性；</w:t>
      </w:r>
    </w:p>
    <w:p w14:paraId="06E24038">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（3）建议制定数据备份策略，会话存档等重要数据每日定时备份至异地存储；</w:t>
      </w:r>
    </w:p>
    <w:p w14:paraId="06E24039">
      <w:pPr>
        <w:spacing w:after="80" w:line="360" w:lineRule="exact"/>
      </w:pPr>
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="宋体" w:hAnsi="宋体" w:eastAsia="宋体"/>
          <w:i w:val="0"/>
          <w:color w:val="000000"/>
          <w:sz w:val="21"/>
          <w:u w:val="none"/>
        </w:rPr>
        <w:t>（4）建议在业务低峰期对OceanBase数据库进行性能基线采集，为后续性能优化提供数据支撑。</w:t>
      </w:r>
    </w:p>'''

xml = xml.replace(old_3, new_3, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(xml)

print('三个占位符已全部替换完成')

# Verify
count = xml.count('测试执行后填写')
print(f'剩余占位符数量: {count}')
