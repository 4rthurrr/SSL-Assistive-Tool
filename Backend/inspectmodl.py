from tensorflow.keras.models import load_model
model = load_model("lip_reading_model.h5")
print("Output Shape:", model.output_shape)