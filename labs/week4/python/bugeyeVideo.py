#!/usr/bin/python
# Copyright 2017 BIG VISION LLC ALL RIGHTS RESERVED
#
# This code is made available to the students of
# the online course titled "Computer Vision for Faces"
# by Satya Mallick for personal non-commercial use.
#
# Sharing this code is strictly prohibited without written
# permission from Big Vision LLC.
#
# For licensing and other inquiries, please email
# spmallick@bigvisionllc.com
#
import cv2,dlib,time,argparse
import numpy as np

FACE_DOWNSAMPLE_RATIO = 1.5
RESIZE_HEIGHT = 360

modelPath = "../../common/shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(modelPath)
bulgeAmount = 3
radius = 30
print("USAGE : python bugeyeVideo.py -b bulgeAmount ( default : 2 ) -r radius (radius around eye, default : 30 )")

def barrel(src, k):
  w = src.shape[1]
  h = src.shape[0]

  # Meshgrid of destiation image
  Xu, Yu = np.meshgrid(np.arange(w), np.arange(h))

  Xu = np.float32(Xu)/w-0.5
  Yu = np.float32(Yu)/h-0.5

  XuSquare = np.square(Xu)
  YuSquare = np.square(Yu)

  r = np.sqrt(XuSquare + YuSquare)

  # Pincushion distortion function
  rn = np.minimum(r, r + np.multiply((np.power(r,k) - r) , np.cos(np.pi * r) ))

  # Applying the distortion on the grid
  Xd = w * ( cv2.divide( np.multiply( rn, Xu ), r) + 0.5 )
  Yd = h * ( cv2.divide( np.multiply( rn, Yu ), r) + 0.5 )

  # Interpolation of points
  dst = cv2.remap(src, Xd, Yd, cv2.INTER_CUBIC)
  return dst


def getLandmarks(im):
  imSmall = cv2.resize(im,None,
                       fx=1.0/FACE_DOWNSAMPLE_RATIO,
                       fy=1.0/FACE_DOWNSAMPLE_RATIO,
                       interpolation = cv2.INTER_LINEAR)
  #detect faces
  rects = detector(imSmall, 0)
  if len(rects) == 0:
    return 1

  #scale the points before sending to the pose predictor as we will send the original image
  newRect = dlib.rectangle(int(rects[0].left()*FACE_DOWNSAMPLE_RATIO),
                           int(rects[0].top()*FACE_DOWNSAMPLE_RATIO),
                           int(rects[0].right()*FACE_DOWNSAMPLE_RATIO),
                           int(rects[0].bottom()*FACE_DOWNSAMPLE_RATIO))
  points = []
  [points.append((p.x, p.y)) for p in predictor(im, newRect).parts()]
  return points


ap = argparse.ArgumentParser()
ap.add_argument("-r", "--radius",  help="radius around eye, default : 30")
ap.add_argument("-b", "--bulge",  help="bulge amount default : 2")

args = vars(ap.parse_args())

if(args["radius"]):
  radius = args["radius"]
if(args["bulge"]):
  bulgeAmount = float(args["bulge"])

cap = cv2.VideoCapture(0)
while(1):
  try:
    ret, src = cap.read()
    height, width = src.shape[:2]
    IMAGE_RESIZE = np.float32(height)/RESIZE_HEIGHT
    src = cv2.resize(src,None,
                       fx=1.0/IMAGE_RESIZE,
                       fy=1.0/IMAGE_RESIZE,
                       interpolation = cv2.INTER_LINEAR)
    # Find the landmark points using DLIB Facial landmarks detector
    landmarks = getLandmarks(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))
    if landmarks == 1:
      cv2.putText(src, "Unable to detect face, Please check proper lighting", (10, 50), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
      cv2.putText(src, "Or Decrease FACE_DOWNSAMPLE_RATIO", (10, 150), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
      cv2.imshow("Bug Eye Demo",src)
      if cv2.waitKey(1) & 0xFF == 27:
        break
      continue

    # Find the roi for left Eye
    roiEyeLeft = [ landmarks[37][0] - radius, landmarks[37][1] - radius,
              (landmarks[40][0] - landmarks[37][0] + 2*radius),
              (landmarks[41][1] - landmarks[37][1] + 2*radius)  ]

    # Find the roi for right Eye
    roiEyeRight = [ landmarks[43][0] - radius, landmarks[43][1] - radius,
              (landmarks[46][0] - landmarks[43][0] + 2*radius),
              (landmarks[47][1] - landmarks[43][1] + 2*radius)  ]

    output = np.copy(src)
    # Find the patch for left eye and apply the transformation
    eyeRegion = src[roiEyeLeft[1]:roiEyeLeft[1] + roiEyeLeft[3],roiEyeLeft[0]:roiEyeLeft[0] + roiEyeLeft[2]]
    eyeRegion = barrel(eyeRegion, bulgeAmount);
    output[roiEyeLeft[1]:roiEyeLeft[1] + roiEyeLeft[3],roiEyeLeft[0]:roiEyeLeft[0] + roiEyeLeft[2]] = eyeRegion

    # Find the patch for right eye and apply the transformation
    eyeRegion = src[roiEyeRight[1]:roiEyeRight[1] + roiEyeRight[3],roiEyeRight[0]:roiEyeRight[0] + roiEyeRight[2]]
    eyeRegion = barrel(eyeRegion, bulgeAmount);
    output[roiEyeRight[1]:roiEyeRight[1] + roiEyeRight[3],roiEyeRight[0]:roiEyeRight[0] + roiEyeRight[2]] = eyeRegion

    cv2.imshow('Bug Eye Demo',output)

    if cv2.waitKey(1) & 0xFF == 27:
      break

  except Exception as e:
    print(e)
cap.release()
cv2.destroyAllWindows()
