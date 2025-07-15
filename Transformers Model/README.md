# 🤗 Transformer Models Demonstrations

This contains example implementations showcasing the use of **pretrained transformer models** from Hugging Face's `transformers` library. These examples demonstrate how Transformers can be applied to **computer vision tasks**, including **object detection** and **image classification** using models like **DETR** and **ViT**.

---

## 🧠 1. Computer Vision – Object Detection with DETR

### 📌 Description

-- Performs **object detection** using `facebook/detr-resnet-50` pretrained on the **COCO dataset**  
-- Downloads an image from a URL and detects objects within it  
-- Returns bounding boxes and confidence scores for each detected object

### 🧰 Technologies Used

-- `transformers`: For loading the DETR model and processor  
-- `torch`: For tensor computations and inference  
-- `PIL`, `requests`: For image downloading and processing

### 🌐 Sample Input

```plaintext
http://images.cocodataset.org/val2017/000000039769.jpg
```


### ✅ Sample Output
```plaintext
Detected person with confidence 0.998 at location [x1, y1, x2, y2]
```

---

## ⚠️ 2. Content Safety – Harmful/Safe Image Classification
### 📌 Description
-- Uses google/vit-large-patch16-224-in21k, a Vision Transformer (ViT) model
-- Performs binary image classification:
-- 0 = safe
-- 1 = harmful
-- Designed for quick content moderation or safety checking use cases

### 🧰 Technologies Used
-- transformers: For loading the ViT model and feature extractor
-- PIL: For image loading and preprocessing

### 📁 Input Image Path
Update your script with the local image path like below:
```plaintext
image_path = r"C:\Users\91639\Downloads\beatenimage.jpg"
```
### ✅ Sample Output
```plaintext
Image is classified as harmful (1.0) with probability 0.997
```
