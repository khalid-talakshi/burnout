import math
import numpy as np

def functionBySegment(point1, point2):
    #Calculates slope and intercept of function
    #that goes through given points
    x1 = point1[0]
    y1 = point1[1]

    x2 = point2[0]
    y2 = point2[1]
    if (x2-x1 == 0):
        #Some straights are vertical on the plot
        slope = 9999999999
    else:
        slope = (y2-y1)/(x2-x1)
    
    intercept = y2 - slope*x2
    return [slope,intercept]

def angle(s1, s2): 
    #Returns angle between two functions using their slopes
    #https://stackoverflow.com/questions/28260962/calculating-angles-between-line-segments-python-with-math-atan2
    return math.degrees(math.atan((s2-s1)/(1+(s2*s1))))

def predictedRotationAngle(p1, p2, p3):
    #Get function going through points p1 and p2
    coef1 = functionBySegment(p1, p2)
    #Same for p2 and p3
    coef2 = functionBySegment(p2, p3)
    #Get angle between these two functions
    return angle(coef1[0], coef2[0])

def getSteering(lapTelemetry):
  x = lapTelemetry['X'].values
  y = lapTelemetry['Y'].values

  #Combine x and y into pairs
  points = np.array([x,y]).T.reshape(-1,1,2)

  angles = []
  for i in range(len(points)-2):
      #Take 3 points, calculate angle and save it
      prediction = predictedRotationAngle(points[i][0],points[i+1][0],points[i+2][0])
      angles.append(prediction)
  return angles