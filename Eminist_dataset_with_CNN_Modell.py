# -*- coding: utf-8 -*-
"""CNN_Model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1vqasga3C78hfOrlkgydqxou7ypZlRevh
"""

import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as transforms
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import numpy as np
import time

# Device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Normalize MNIST data
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

# Load MNIST dataset
train_dataset = torchvision.datasets.MNIST(root='./data', train=True, transform=transform, download=True)
test_dataset = torchvision.datasets.MNIST(root='./data', train=False, transform=transform, download=True)

train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=100, shuffle=True)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=100, shuffle=False)

# Define CNN feature extractor
class CNNFeatureExtractor(nn.Module):
    def __init__(self):
        super(CNNFeatureExtractor, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=5),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=5),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(32 * 4 * 4, 128)

    def forward(self, x):
        x = self.features(x)
        x = self.flatten(x)
        x = self.fc(x)
        return x

# Model, loss, and optimizer
cnn_model = CNNFeatureExtractor().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(cnn_model.parameters(), lr=0.001)

# Training loop for 100 epochs
num_epochs = 100
loss_list = []
epoch_times = []

print("Training CNN for feature extraction...")
cnn_model.train()
for epoch in range(num_epochs):
    start_time = time.time()
    running_loss = 0

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)

        outputs = cnn_model(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    end_time = time.time()
    epoch_duration = end_time - start_time
    epoch_times.append(epoch_duration)
    avg_loss = running_loss / len(train_loader)
    loss_list.append(avg_loss)

    # Show each epoch results
    print(f"Epoch [{epoch+1}/{num_epochs}] - Loss: {avg_loss:.4f} - Time: {epoch_duration:.2f} sec")

# Feature extraction
def extract_features(model, loader):
    model.eval()
    features, labels = [], []
    with torch.no_grad():
        for images, lbls in loader:
            images = images.to(device)
            feats = model(images).cpu().numpy()
            features.append(feats)
            labels.append(lbls.numpy())
    return np.concatenate(features), np.concatenate(labels)

train_features, train_labels = extract_features(cnn_model, train_loader)
test_features, test_labels = extract_features(cnn_model, test_loader)

# Train and evaluate SVM
print("\nTraining SVM on CNN features...")
svm = SVC(kernel='linear')
svm.fit(train_features, train_labels)
pred_labels = svm.predict(test_features)
acc = accuracy_score(test_labels, pred_labels)

# Plot loss and time per epoch
epochs = range(1, num_epochs + 1)
plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(epochs, loss_list, label="Loss", color='blue')
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("CNN Training Loss per Epoch")
plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(epochs, epoch_times, label="Time", color='orange')
plt.xlabel("Epoch")
plt.ylabel("Seconds")
plt.title("Epoch Time")
plt.grid(True)

plt.tight_layout()
plt.show()

# Confusion Matrix
cm = confusion_matrix(test_labels, pred_labels)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=range(10))
disp.plot(cmap='Blues', values_format='d')
plt.title("SVM Confusion Matrix on MNIST")
plt.show()

# Final report
print(f"\n✅ Final Test Accuracy (CNN + SVM): {acc:.4f}")
print(f"🕒 Total CNN Training Time: {sum(epoch_times):.2f} seconds")