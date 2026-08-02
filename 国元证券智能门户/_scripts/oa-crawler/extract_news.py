import pdfplumber

pdf_path = r'C:\Users\11039\Desktop\文档资料\国元证券\操作手册，培训材料\智能门户\3.智能门户平台操作手册(更新至V1.4.0无水印).pdf'
pdf = pdfplumber.open(pdf_path)

# 提取新闻公告章节：第128-154页
news_text = ""
for page_num in range(128, 155):  # 128到154页
    page = pdf.pages[page_num-1]
    text = page.extract_text()
    if text:
        news_text += f"\n\n=== 第{page_num}页 ===\n"
        news_text += text

# 保存到文件
with open("news_announcement.txt", "w", encoding="utf-8") as f:
    f.write(news_text)

print(f"新闻公告文本已保存到 news_announcement.txt，总字符数: {len(news_text)}")