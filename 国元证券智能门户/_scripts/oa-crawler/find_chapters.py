import pdfplumber
import re

pdf_path = r'C:\Users\11039\Desktop\文档资料\国元证券\操作手册，培训材料\智能门户\3.智能门户平台操作手册(更新至V1.4.0无水印).pdf'
pdf = pdfplumber.open(pdf_path)

print("=== 查找章节标题 ===")
for i, page in enumerate(pdf.pages):
    text = page.extract_text()
    if text:
        # 查找可能的章节标题模式
        lines = text.split('\n')
        for line in lines[:10]:  # 检查前10行
            line = line.strip()
            # 匹配 "一、", "二、", "三、" 等
            if re.match(r'^[一二三四五六七八九十]+、', line):
                print(f"第{i+1}页: {line}")
                break
            # 匹配 "第X章"
            if re.match(r'^第[一二三四五六七八九十百]+章', line):
                print(f"第{i+1}页: {line}")
                break