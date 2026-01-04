import cv2
from feture_extract import get_detels
import imutils


cap = cv2.VideoCapture(0)




print("Press 'q' to exit.")

while True:
    r,image = cap.read()
    #image = cv2.imread("face.jpeg")

    image = imutils.resize(image,width=1000)

    org_image, calc_img, feture_cordinate = get_detels(image,anotation=True)

    if feture_cordinate[0] == 1:
        print(feture_cordinate)



    cv2.imshow('calculation', calc_img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break



