from __future__ import absolute_import, division, print_function
from sklearn.model_selection import train_test_split
import numpy as np # linear algebra
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from torch.utils.tensorboard import SummaryWriter


checkpoint_dir = 'tmp/modelchkpt'
os.makedirs(checkpoint_dir, exist_ok=True)

class CNNModel(nn.Module):
    def __init__(self):
        super(CNNModel, self).__init__()

        # First conv block
        self.conv1 = nn.Conv2d(3, 50, kernel_size=7, padding='same')
        self.conv2 = nn.Conv2d(50, 90, kernel_size=3, padding='valid')
        self.conv3 = nn.Conv2d(90, 10, kernel_size=5, padding='same')
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Second conv block
        self.conv4 = nn.Conv2d(10, 5, kernel_size=3, padding='same')
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)

        # Fully connected layers
        # Calculate the size after convolutions and pooling
        # Input: 50x50x3
        # After conv2 (valid): 48x48
        # After pool1: 24x24
        # After pool2 (with padding): 12x12
        self.fc1 = nn.Linear(5 * 12 * 12, 2000)
        self.fc2 = nn.Linear(2000, 1000)
        self.fc3 = nn.Linear(1000, 500)
        self.fc4 = nn.Linear(500, 2)

        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        # First conv block
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        x = self.relu(self.conv3(x))
        x = self.pool1(x)

        # Second conv block
        x = self.relu(self.conv4(x))
        x = self.pool2(x)

        # Flatten
        x = x.view(x.size(0), -1)

        # Fully connected layers
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        x = self.fc4(x)

        return x  # No softmax needed for CrossEntropyLoss




#################################MODEL TRAINING##################################################

#Model and images based on https://www.kaggle.com/code/kushal1996/detecting-malaria-cnn
cells=np.load('Cells3.npy')
labels=np.load('Labels3.npy')



train_x , x , train_y , y = train_test_split(cells , labels ,
                                            test_size = 0.2 ,
                                            random_state = 111)

eval_x , test_x , eval_y , test_y = train_test_split(x , y ,
                                                    test_size = 0.5 ,
                                                    random_state = 111)
# GPU configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if torch.cuda.is_available():
    print(f'Default GPU Device: {torch.cuda.get_device_name(0)}')
    print(f"Number of GPUs available: {torch.cuda.device_count()}")
else:
    print("No GPU available, using CPU")




# Initialize model
model = CNNModel()
model.load_state_dict(torch.load(os.path.join(checkpoint_dir, 'checkpoint.pth'))['model_state_dict'])
model = model.to(device)

# Print model architecture
print(model)
print(f"\nTotal parameters: {sum(p.numel() for p in model.parameters())}")

# Define loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.00001)

# Prepare data loaders (assuming train_x, train_y, eval_x, eval_y, test_x, test_y are defined)
# Convert numpy arrays to PyTorch tensors
# Note: PyTorch expects shape (N, C, H, W) while Keras uses (N, H, W, C)
train_x_tensor = torch.FloatTensor(train_x).permute(0, 3, 1, 2)  # Transpose to (N, C, H, W)
train_y_tensor = torch.LongTensor(train_y)
eval_x_tensor = torch.FloatTensor(eval_x).permute(0, 3, 1, 2)
eval_y_tensor = torch.LongTensor(eval_y)
test_x_tensor = torch.FloatTensor(test_x).permute(0, 3, 1, 2)
test_y_tensor = torch.LongTensor(test_y)

# Create datasets and dataloaders
train_dataset = TensorDataset(train_x_tensor, train_y_tensor)
eval_dataset = TensorDataset(eval_x_tensor, eval_y_tensor)
test_dataset = TensorDataset(test_x_tensor, test_y_tensor)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
eval_loader = DataLoader(eval_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=True)

#TensorBoard setup
writer = SummaryWriter(log_dir='tmp/modelchkpt/logs')

# Training configuration
num_epochs = 50
best_val_accuracy = 0.0



# Training function
def train_epoch(model, train_loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0


    for batch_idx, (inputs, labels) in enumerate(train_loader):
        inputs, labels = inputs.to(device), labels.to(device)

        # Zero the gradients
        optimizer.zero_grad()

        # Forward pass
        outputs = model(inputs)
        loss = criterion(outputs, labels)

        # Backward pass and optimize
        loss.backward()
        # if batch_idx == 0:  # First batch only
        #     for name, param in model.named_parameters():
        #         if param.grad is not None:
        #             print(f"{name}: grad mean={param.grad.mean():.6f}, grad max={param.grad.max():.6f}")
        #         else:
        #             print(f"{name}: NO GRADIENT!")


        optimizer.step()

        # Statistics
        running_loss += loss.item() * inputs.size(0)
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


# Validation function
def validate(model, val_loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(device), labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


#Training loop
for epoch in range(num_epochs):
    print(f'\nEpoch {epoch + 1}/{num_epochs}')
    print('-' * 50)

    # Train
    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
    print(f'Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}')

    # Validate
    val_loss, val_acc = validate(model, eval_loader, criterion, device)
    print(f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}')

    # TensorBoard logging
    writer.add_scalar('Loss/train', train_loss, epoch)
    writer.add_scalar('Loss/val', val_loss, epoch)
    writer.add_scalar('Accuracy/train', train_acc, epoch)
    writer.add_scalar('Accuracy/val', val_acc, epoch)

    # Save best model
    if val_acc > best_val_accuracy:
        best_val_accuracy = val_acc
        checkpoint_path = os.path.join(checkpoint_dir, 'checkpoint.pth')
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_accuracy': val_acc,
        }, checkpoint_path)
        print(f'Checkpoint saved with val_accuracy: {val_acc:.4f}')

writer.close()

