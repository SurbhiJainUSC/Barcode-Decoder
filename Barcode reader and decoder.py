from pyzbar import pyzbar
import numpy as np
import argparse
import imutils
import cv2

import pyttsx

from bs4 import BeautifulSoup
import requests

import urllib, json

from lxml import html

import operator
import os

def captureImage():
    camera = cv2.VideoCapture(0)
    while True:
        return_value,image = camera.read()
        gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        cv2.imshow('image',gray)
        if cv2.waitKey(1)& 0xFF == ord('s'):
            cv2.imwrite('test.jpg',image)
            break
    camera.release()
    cv2.destroyAllWindows()

def getBarcode():
    image = cv2.imread('test.jpg')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
     
    # compute the Scharr gradient magnitude representation of the images
    # in both the x and y direction using OpenCV 2.4
    ddepth = cv2.cv.CV_32F if imutils.is_cv2() else cv2.CV_32F
    gradX = cv2.Sobel(gray, ddepth=ddepth, dx=1, dy=0, ksize=-1)
    gradY = cv2.Sobel(gray, ddepth=ddepth, dx=0, dy=1, ksize=-1)
     
    # subtract the y-gradient from the x-gradient
    gradient = cv2.subtract(gradX, gradY)
    gradient = cv2.convertScaleAbs(gradient)

    # blur and threshold the image
    blurred = cv2.blur(gradient, (4, 4))
    (_, thresh) = cv2.threshold(blurred, 225, 255, cv2.THRESH_BINARY)

    # construct a closing kernel and apply it to the thresholded image
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 7))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # perform a series of erosions and dilations
    closed = cv2.erode(closed, None, iterations = 1)
    closed = cv2.dilate(closed, None, iterations = 1)

    # find the contours in the thresholded image, then sort the contours
    # by their area, keeping only the largest one
    cnts = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    c = sorted(cnts, key = cv2.contourArea, reverse = True)[0]

    # compute the rotated bounding box of the largest contour
    rect = cv2.minAreaRect(c)
    box = cv2.cv.BoxPoints(rect) if imutils.is_cv2() else cv2.boxPoints(rect)
    box = np.int0(box)
     
    # draw a bounding box arounded the detected barcode and display the
    # image
    cv2.drawContours(image, [box], -1, (0, 255, 0), 3)
    cv2.imshow("Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def decodeBarcode():
    # load the input image
    image = cv2.imread('test.jpg')
    barcodeData = ''
    # find the barcodes in the image and decode each of the barcodes
    barcodes = pyzbar.decode(image)

    # loop over the detected barcodes
    for barcode in barcodes:
            # extract the bounding box location of the barcode and draw the
            # bounding box surrounding the barcode on the image
            (x, y, w, h) = barcode.rect
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
     
            # the barcode data is a bytes object so if we want to draw it on
            # our output image we need to convert it to a string first
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type
     
            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 2)
     
            # print the barcode type and data to the terminal
            #print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
            
    # show the output image
    cv2.imshow("Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return barcodeData

    

def getDataAPI(productName):
    words = productName.split(' ')
    query = ''
    for w in words:
        query += w + '+'
    query = query[:len(query)-1]
    
    url = 'https://www.google.com/search?q=' + query + '&tbm=shop&source=lnms&sa=X&ved=0ahUKEwioxMrrheXgAhUXvZ4KHZSIAEIQ_AUICigB&biw=1211&bih=719&dpr=2'
  
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    allP = soup.find_all('div', class_='A8OWCb')

    productPrices = {}
    for p in allP:
        p = p.text
        
        dotIdx = p.find('.')
        price = p[:dotIdx+3]
        price = price.replace(',', '')
        price = float(price[1:])
        
        seller = p[dotIdx+3:]
    
        if seller.split(' ')[0].lower() == 'from':
            continue
        else:
            if seller.lower() in productPrices:
                existingP = productPrices[seller.lower()]
                if price<existingP:
                    productPrices[seller.lower()] = price
            else:
                productPrices[seller.lower()] = price

    sortedProductPrices = sorted(productPrices.items(), key = operator.itemgetter(1))

    return sortedProductPrices
            

def getProductName(barcodeData):
    url = "https://www.barcodelookup.com/" + barcodeData
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    allP = soup.find_all('h4')
    
    for p in allP:
        p = p.text
        return p

    return ''
    


if __name__ == '__main__':
    captureImage()

    barcodeData = decodeBarcode()
    if len(barcodeData)==0:
        print('Barcode not detected!')
    else:
        print('Barcode: ' + barcodeData)
    
        productName = getProductName(barcodeData)
        productName = productName.strip('\n')
        if len(productName)==0:
            print('Barcode not found!')
        else:
            print('Product Name: ' + productName)

            productPrices = getDataAPI(productName)

            for prod in productPrices:
                name = prod[0]
                price = format(prod[1], '.2f')
                price = '$' + price
                print(name, price)
        
            engine = pyttsx.init()
            engine.say(productName)
            engine.runAndWait()

    
