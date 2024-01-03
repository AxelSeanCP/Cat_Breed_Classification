# -*- coding: utf-8 -*-
"""proyek_akhir_kelas_menengahy(1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1mkc0Y4QFaHIfo66sgaVne4XNeYfGdV5O

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

!pip install split-folders
!pip install pillow

"""### import libraries"""

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
#from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, Flatten, Dropout, Conv2D, MaxPooling2D, BatchNormalization
from tensorflow.keras.regularizers import l2
import numpy as np
import matplotlib.pyplot as plt
import pathlib, zipfile, os, splitfolders, datetime
from PIL import Image

"""### setup tensorboard"""

# Commented out IPython magic to ensure Python compatibility.
# %load_ext tensorboard

log_dir = "logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

!rm -rf ./logs/

tf.summary.create_file_writer("./logs/")

tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

"""### extract zip file"""

zip_path = "/content/oxford-iiit-cats-extended-10k.zip"
zip_read = zipfile.ZipFile(zip_path, "r")
zip_read.extractall('/content/dataset')
zip_read.close()

os.listdir('/content/dataset/')

"""### split into train and validation"""

original_dir = '/content/dataset/CatBreedsRefined-v3'

splitfolders.ratio(original_dir, output='/content/dataset/project', seed=6969, ratio=(0.8, 0.2))
train_dir = '/content/dataset/project/train'
validation_dir = '/content/dataset/project/val'

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

batch_size = 16
target_size=(192,192)

train_datagen = ImageDataGenerator(
    rescale = 1.0/255,
    shear_range=0.2,
    zoom_range=0.2,
    width_shift_range=0.2,
    height_shift_range=0.2,
    channel_shift_range=0.2,
    horizontal_flip=True,
    vertical_flip=True,
    fill_mode='nearest'
)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    class_mode='categorical',
    target_size=target_size,
    batch_size=batch_size
)

validation_datagen = ImageDataGenerator(
    rescale=1.0/255
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
      self.sabar_loss += 1

    if self.sabar_acc == 0:
      print(f"The model accuracy has been below {self.max_acc} and {self.max_val_acc} for {self.limit_acc} epochs, Stopping training immediatly!!!")
      self.model.stop_training = True
    elif self.sabar_loss == 0:
      print(f"The model loss has been above 75% for {self.limit_loss} epochs, Stopping training immediatly!!!")
      self.model.stop_training = True
    elif logs.get('accuracy') >= 0.92 and logs.get('val_accuracy') >= 0.92:
      print(f"The model accuracy has reached 92%, stopping training")
      self.model.stop_training = True

"""### transfer learning using MobileNetV2

model = tf.keras.Sequential()

# add mobile net as base layer
pre_trained_model = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_tensor=Input(shape=(224,224,3))
)

for layer in pre_trained_model.layers:
  layer.trainable = False

for layer in pre_trained_model.layers[-10:]:
  layer.trainable = True

model.add(pre_trained_model)

# add custom layers
model.add(Dropout(0.3))
model.add(Conv2D(72, (3,3), activation="relu"))
model.add(MaxPooling2D(2,2))
model.add(Dropout(0.3))
model.add(Flatten())
model.add(Dense(512, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(0.001)))
model.add(Dense(64, activation="relu"))
model.add(Dense(12, activation="softmax"))

model.summary()
"""

do = 0.3
model = tf.keras.models.Sequential([
    Conv2D(128, (3,3), activation="relu", input_shape=(192,192,3)),
    MaxPooling2D(2,2),
    Conv2D(32, (3,3), activation="relu"),
    MaxPooling2D(2,2),
    Dropout(do),
    Conv2D(128, (3,3), activation="relu"),
    MaxPooling2D(2,2),
    Conv2D(32, (3,3), activation="relu"),
    MaxPooling2D(2,2),
    Dropout(do),
    Flatten(),
    Dense(256, activation="relu"),
    Dense(64, activation="relu"),
    Dense(12, activation="softmax")
])

model.summary()

int_lr = 1e-2
#lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay(initial_learning_rate=int_lr, decay_steps=500, decay_rate=0.5)
model.compile(
    optimizer=tf.optimizers.Adam(learning_rate=int_lr),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

berhenti_bang = SantaiDuluGakSih(sabar_acc=4, sabar_loss=10)
modelku = model.fit(
    train_generator,
    epochs=20,
    validation_data=validation_generator,
    callbacks=[berhenti_bang, tensorboard_callback],
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

"""### show tensorboard"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir logs/fit

"""# Save model"""

# menyimpan model dalam format saved model
export_dir = 'saved_model/'
tf.saved_model.save(model, export_dir)

# convert SavedModel menjadi vegs.tflite
converter = tf.lite.TFLiteConverter.from_saved_model(export_dir)
tflite_model = converter.convert()

tflite_model_file = pathlib.Path('vegs.tflite')
tflite_model_file.write_bytes(tflite_model)