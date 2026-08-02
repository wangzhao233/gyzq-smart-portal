import easyocr
import os

reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

base = r'C:\Users\11039\WorkBuddy\国元证券智能门户\output\word\media'

for i, img_name in enumerate(['image1.png', 'image2.png'], 1):
    img_path = os.path.join(base, img_name)
    print(f'===== IMAGE {i}: {img_name} =====')
    results = reader.readtext(img_path)
    for bbox, text, conf in results:
        if conf > 0.2:
            print(f'  [{conf:.2f}] {text}')
    print()
