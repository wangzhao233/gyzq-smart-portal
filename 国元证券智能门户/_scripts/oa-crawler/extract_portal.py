import pdfplumber

pdf_path = r'C:\Users\11039\Desktop\文档资料\国元证券\操作手册，培训材料\智能门户\3.智能门户平台操作手册(更新至V1.4.0无水印).pdf'
pdf = pdfplumber.open(pdf_path)

# 提取门户中心章节：第5-56页
portal_text = ""
for page_num in range(5, 57):  # 5到56页
    page = pdf.pages[page_num-1]
    text = page.extract_text()
    if text:
        portal_text += f"\n\n=== 第{page_num}页 ===\n"
        portal_text += text

# 保存到文件
with open("portal_center.txt", "w", encoding="utf-8") as f:
    f.write(portal_text)

print(f"门户中心文本已保存到 portal_center.txt，总字符数: {len(portal_text)}")