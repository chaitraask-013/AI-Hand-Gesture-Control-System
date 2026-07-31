import cv2
cap = cv2.VideoCapture(0)
while True:
    success,frame=cap.read()
    cv2.line(frame,(50,50),(300,50),(0,255,0),3)
    cv2.rectangle(frame,(100,100),(300,250),(255,0,0),3)
    cv2.circle(frame,(500,200),50,(0,0,255),-1)
    cv2.putText(frame,"Helloo Chaii",
                (50,400),
                cv2.FONT_HERSHEY_SIMPLEX,1,
                (255,255,255),2)
    print(frame.shape)
    cv2.imshow("webcam",frame)
    if cv2.waitKey(1)& 0xFF==ord('q'):
         break
cap.release()
cv2.destroyAllWindows()



