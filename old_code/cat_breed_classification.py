# -*- coding: utf-8 -*-
"""cat_breed_classification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1h99fnnYBzAnKh8YaVxRBYCHxmrDh6D1_

[link dataset](https://www.kaggle.com/datasets/doctrinek/oxford-iiit-cats-extended-10k)

# Setup

### command line
"""

# import the kaggle.json from kaggle API into colab
# do this command

# install kaggle library
!pip install kaggle
# make a directory named .kaggle
!mkdir ~/.kaggle
# copy the kaggle.json into this new directory
!cp kaggle.json ~/.kaggle/
# alocate the required permission for this file
!chmod 600 ~/.kaggle/kaggle.json
# download dataset
!kaggle datasets download doctrinek/oxford-iiit-cats-extended-10k

!pip install -q split-folders

"""### import libraries"""

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, Flatten, Dropout, Conv2D, MaxPooling2D, BatchNormalization, Input
from tensorflow.keras.regularizers import l2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pathlib, zipfile, os, splitfolders, datetime

"""### extract zip file"""

zip_path = "/content/oxford-iiit-cats-extended-10k.zip"
zip_read = zipfile.ZipFile(zip_path, "r")
zip_read.extractall('/content/dataset')
zip_read.close()

os.listdir('/content/dataset/')

original_dir = '/content/dataset/CatBreedsRefined-v3'

"""### split into train and validation"""

splitfolders.ratio(original_dir, output='/content/project', seed=6969, ratio=(0.8, 0.2))
train_dir = '/content/project/train'
validation_dir = '/content/project/val'

"""### explore data samples"""

def total_sample(directory):
  total = 0
  for folder in os.listdir(directory):
    folder_path = os.path.join(directory, folder)
    total += len(os.listdir(folder_path))

  return total

train_sample_length = total_sample(train_dir)
validation_sample_length = total_sample(validation_dir)
print(f"The train directory has {train_sample_length} samples")
print(f"The validation directory has {validation_sample_length} samples")
print(f"Which in total makes it {train_sample_length + validation_sample_length} samples")

"""### display images"""

def display_image(path, num_images=3, subplot_size=(10,5)):
  files = os.listdir(path)

  fig, axes = plt.subplots(1, num_images, figsize=subplot_size)

  for i in range(min(num_images, len(files))):
    file_path = os.path.join(path, files[i])

    img = mpimg.imread(file_path)
    axes[i].imshow(img)
    axes[i].set_title(f"image {i+1}")
    axes[i].axis('off')

  plt.suptitle(f"Images from {path}")
  plt.show()

folder_path = [f.path for f in os.scandir(train_dir) if f.is_dir()]

for path in folder_path:
  display_image(path, num_images=5)

"""# Preprocess Data
```
rescale = 1.0/255,
shear_range=0.2,
zoom_range=0.2,
width_shift_range=0.2,
height_shift_range=0.2,
channel_shift_range=0.2,
horizontal_flip=True,
fill_mode='nearest'
```
"""

batch_size = 50
target_size=(224,224)
steps_per_epoch = train_sample_length / batch_size
validation_step = validation_sample_length / batch_size
rescale_factor = 1.0 / 255

train_datagen = ImageDataGenerator(
    rescale = rescale_factor,
    zoom_range=0.2,
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    class_mode='categorical',
    target_size=target_size,
    batch_size=batch_size
)

validation_datagen = ImageDataGenerator(
    rescale=rescale_factor
)

validation_generator = validation_datagen.flow_from_directory(
    validation_dir,
    class_mode='categorical',
    target_size=target_size,
    batch_size=batch_size
)

"""# Model Creation

### callback function
- stops when acc & val_acc is >= 92%
- stops when acc / val_acc < max_acc for limit_acc epochs
- stops when loss / val_loss > 0.75 for limit_loss epochs
"""

class SantaiDuluGakSih(tf.keras.callbacks.Callback):
  def __init__(self, sabar_acc=10, sabar_loss=10):
    super(SantaiDuluGakSih, self).__init__()
    self.sabar_acc = sabar_acc
    self.sabar_loss = sabar_loss
    self.limit_acc = sabar_acc
    self.limit_loss = sabar_loss
    self.max_acc = 0
    self.max_val_acc = 0

  def on_epoch_end(self, epoch, logs={}):
    self.max_acc = logs.get('accuracy') if logs.get('accuracy') > self.max_acc else self.max_acc

    self.max_val_acc = logs.get('val_accuracy') if logs.get('val_accuracy') > self.max_val_acc else self.max_val_acc

    if logs.get('accuracy')>=self.max_acc and logs.get('val_accuracy')>=self.max_val_acc:
      self.sabar_acc = self.limit_acc
    else:
      self.sabar_acc -= 1

    if logs.get('loss')>0.75 or logs.get('val_loss')>0.75:
      self.sabar_loss -= 1
    else:
      self.sabar_loss += self.limit_loss

    if self.sabar_acc == 0:
      print(f"The model accuracy has been below {self.max_acc} and {self.max_val_acc} for {self.limit_acc} epochs, Stopping training immediatly!!!")
      self.model.stop_training = True
    elif self.sabar_loss == 0:
      print(f"The model loss has been above 75% for {self.limit_loss} epochs, Stopping training immediatly!!!")
      self.model.stop_training = True
    elif logs.get('accuracy') >= 0.92 and logs.get('val_accuracy') >= 0.92:
      print(f"The model accuracy has reached 92%, stopping training")
      self.model.stop_training = True

class learningrateLogger(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs=None):
    print(f"Epoch {epoch+1}/{self.params['epochs']}, Learning Rate: {self.model.optimizer.lr.numpy()}")

from tensorflow.keras.callbacks import ReduceLROnPlateau
reduce_lr = ReduceLROnPlateau(
    monitor="val_accuracy",
    factor=0.8,
    patience=2,
    verbose=1,
    mode="max",
    min_lr=0.00001
)

"""### transfer learning using MobileNetV2"""

model = tf.keras.Sequential()

# add mobile net as base layer
pre_trained_model = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_shape=(224,224,3)
)

for layer in pre_trained_model.layers:
  layer.trainable = True

print("Jumlah layer di pre_trained_model: ", len(pre_trained_model.layers))

fine_tune_di = 120

for layer in pre_trained_model.layers[:fine_tune_di]:
  layer.trainable = False

print("trainable layer: ", len(pre_trained_model.trainable_variables))

model.add(pre_trained_model)

# add custom layers
do = 0.4
l2val = 0.0001
model.add(Dropout(do))
model.add(Conv2D(64, (3,3), activation="relu", input_shape=(224,224,3), kernel_regularizer=l2(l2val)))
model.add(MaxPooling2D(2,2))
model.add(Dropout(do))
model.add(Flatten())
model.add(Dense(128, activation="relu", kernel_regularizer=l2(l2val)))
model.add(Dropout(do))
model.add(Dense(64, activation="relu"))
model.add(Dropout(do))
model.add(Dense(12, activation="softmax"))

model.summary()

int_lr = 1e-4
model.compile(
    optimizer=tf.optimizers.Adam(int_lr),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

loss0, acc0 = model.evaluate(validation_generator)

berhenti_bang = SantaiDuluGakSih(sabar_acc=5, sabar_loss=10)
modelku = model.fit(
    train_generator,
    epochs=30,
    steps_per_epoch=steps_per_epoch,
    validation_steps=validation_step,
    validation_data=validation_generator,
    callbacks=[berhenti_bang, reduce_lr, learningrateLogger()],
    verbose=2
)

"""# Model evaluation

### plot loss and accuracy
"""

# plot loss
plt.plot(modelku.history['loss'])
plt.plot(modelku.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper right')
plt.show()

# plot acc
plt.plot(modelku.history['accuracy'])
plt.plot(modelku.history['val_accuracy'])
plt.title('Model accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='lower right')
plt.show()

val_loss_acc = model.evaluate(validation_generator, steps=len(validation_generator))

# Commented out IPython magic to ensure Python compatibility.
from google.colab import files
from tensorflow.keras.preprocessing import image
import matplotlib.image as mpimg
# %matplotlib inline

uploaded = files.upload()

class_labels = ['Abyssinian', 'Bengal', 'Birman', 'Bombay', 'British Shorthair', 'Egyptian Mau',
                'Maine Coon', 'Persian', 'Ragdoll', 'Russian Blue', 'Siamese', 'Sphynx']

for fn in uploaded.keys():

  #predict gambar
  path = fn
  img = image.load_img(path, target_size=target_size)

  imgplot = plt.imshow(img)
  plt.show()

  x = image.img_to_array(img)
  x = np.expand_dims(x, axis=0)
  images = np.vstack([x])

  classes = model.predict(images, batch_size=10)
  predicted_index = np.argmax(classes)
  confidence_score = classes[0][predicted_index]

  predicted_label = class_labels[predicted_index]

  print(f"Predicted Class: {predicted_label}")
  print(f"Confidence Score: {confidence_score}")

"""# Save model"""

# menyimpan model dalam format saved model
export_dir = 'saved_model/'
tf.saved_model.save(model, export_dir)

# convert SavedModel menjadi vegs.tflite
converter = tf.lite.TFLiteConverter.from_saved_model(export_dir)
tflite_model = converter.convert()

tflite_model_file = pathlib.Path('vegs.tflite')
tflite_model_file.write_bytes(tflite_model)