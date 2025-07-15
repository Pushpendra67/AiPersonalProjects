import torch
from transformers import AutoModelForImageClassification, ViTFeatureExtractor
from PIL import Image

model_name = "google/vit-large-patch16-224-in21k"
model = AutoModelForImageClassification.from_pretrained(model_name)
feature_extractor = ViTFeatureExtractor.from_pretrained(model_name)

image_path = r"C:\Users\91639\Downloads\beatenimage.jpg"
image = Image.open(image_path)  
inputs = feature_extractor(images=[image], return_tensors="pt") 


outputs = model(**inputs)
logits = outputs.logits
probabilities = torch.softmax(logits, dim=1)

predicted_label_index = probabilities.argmax()
predicted_label_float = float(predicted_label_index)
predicted_probability = probabilities[0][predicted_label_index].item()

if predicted_label_index == 0:
    print("Image is classified as safe", predicted_label_float, "with probability", predicted_probability)
elif predicted_label_index == 1:
    print("Image is classified as harmful", predicted_label_float, "with probability", predicted_probability)
else:
    print("Unexpected label", predicted_label_float, "with probability", predicted_probability)
