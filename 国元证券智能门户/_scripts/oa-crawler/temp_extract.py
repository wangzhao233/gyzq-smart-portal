import pdfplumber

pdf_path = r'C:\Users\11039\Desktop\文档资料\国元证券\操作手册，培训材料\智能门户\3.智能门户平台操作手册(更新至V1.4.0无水印).pdf'
pdf = pdfplumber.open(pdf_path)
print(f"总页数: {len(pdf.pages)}")

# 提取前20页文本，查找目录
for i, page in enumerate(pdf.pages[:20]):
    text = page.extract_text()
    if text:
        print(f"--- 第{i+1}页 ---")
        print(text[:1000])
        print("\n")
        
# 查找包含"第三章"或"第十二章"的页面
print("\n\n=== 查找章节标题 ===")
for i, page in enumerate(pdf.pages):
    text = page.extract_text()
    if text and ("第三章" in text or "第十二章" in text):
        print(f"在第{i+1}页找到章节标题")
        # 打印该页前200字符
        print(text[:200])