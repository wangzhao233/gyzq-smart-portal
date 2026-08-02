import pdfplumber

pdf_path = r'C:\Users\11039\Desktop\文档资料\国元证券\操作手册，培训材料\智能门户\3.智能门户平台操作手册(更新至V1.4.0无水印).pdf'
pdf = pdfplumber.open(pdf_path)
print(f"总页数: {len(pdf.pages)}")

# 搜索包含"门户中心"和"新闻公告"的页面
portal_pages = []
news_pages = []

for i, page in enumerate(pdf.pages):
    text = page.extract_text()
    if text:
        if "门户中心" in text and i < 100:  # 门户中心应该在前半部分
            portal_pages.append(i+1)
        if "新闻公告" in text:
            news_pages.append(i+1)

print(f"门户中心相关页码: {portal_pages[:10]}...")  # 显示前10个
print(f"新闻公告相关页码: {news_pages[:10]}...")  # 显示前10个

# 查找章节标题模式
print("\n=== 查找章节标题 ===")
for i, page in enumerate(pdf.pages):
    text = page.extract_text()
    if text:
        # 查找可能的章节标题
        lines = text.split('\n')
        for line in lines[:5]:  # 只检查前5行
            if ("第" in line and "章" in line) or ("一、" in line and "门户" in line) or ("三、" in line and "门户" in line):
                print(f"第{i+1}页: {line.strip()}")
                break