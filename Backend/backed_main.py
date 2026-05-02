from Predict_realtime import predict_video

# ss = predict_video('practis_letters/L1.mp4')
ss = predict_video('output_frz2.mp4')
confidnt_array = ss[3][0]

print(confidnt_array)
