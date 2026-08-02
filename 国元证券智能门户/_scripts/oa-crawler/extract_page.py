import pdfplumber

pdf_path = r'C:\Users\11039\Desktop\文档资料\国元证券\操作手册，培训材料\智能门户\3.智能门户平台操作手册(更新至V1.4.0无水印).pdf'
pdf = pdfplumber.open(pdf_path)

# 提取第128页
page_num = 128
if page_num <= len(pdf.pages):
    page = pdf.pages[page_num-1]
    text = page.extract_text()
    print(f"第{page_num}页内容:")
    print(text[:2000])
else:
    print(f"页码超出范围，总页数: {len(pdf.pages)}")