---
name: paddleocr-vision
description: "Extract multilingual text from images and PDF documents."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [OCR, Vision, TextExtraction, PaddleOCR, Documents, AI]
    related_skills: [web-extraction, knowledge-system]
---

# PaddleOCR Multilingual Document OCR

Extract structured text, table layouts, and invoices from images and scanned PDF documents using PaddleOCR.

---

## 1. Quick Reference

| Action | Command |
|---|---|
| **Install Package** | `pip install paddlepaddle paddleocr` |
| **CLI OCR Image** | `paddleocr --image_dir ./document.png --use_angle_cls true --lang en` |
| **Structure / Table OCR** | `paddleocr --image_dir ./table.png --type structure` |

---

## 2. Python Integration

```python
from paddleocr import PaddleOCR

def extract_text(image_path: str, lang: str = "en") -> list[dict]:
    ocr = PaddleOCR(use_angle_cls=True, lang=lang)
    result = ocr.ocr(image_path, cls=True)
    extracted = []
    for idx, page in enumerate(result):
        for line in page:
            text = line[1][0]
            confidence = line[1][1]
            extracted.append({"page": idx + 1, "text": text, "confidence": float(confidence)})
    return extracted
```
