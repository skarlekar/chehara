import os
import json
import requests
import base64
import sys
from objectpath import *

def printJson(jsonObject, label):
    print(json.dumps(jsonObject, indent=4, sort_keys=True))

def getBytes(image_url):
    req_for_image = requests.get(image_url, stream=True)
    file_object_from_req = req_for_image.raw
    req_data_bytes = file_object_from_req.read()
    #print("getBytes completed")
    return req_data_bytes

def encodeBytes(file_bytes):
    bytestr = base64.b64encode(file_bytes)
    return bytestr

def detectLandmark(image_url):
    landmarkDetected = False
    landmarkResponse = None
    print("############## image_url = {}".format(image_url))
    imageStr = encodeBytes(getBytes(image_url))
    detectionType = "LANDMARK_DETECTION"
    requestJson = {'requests': [{'image': {'content': imageStr}, 'features': [{'type': detectionType}]}]}
    gvision_url = "https://vision.googleapis.com/v1/images:annotate"
    gcp_api_key = os.environ["GCP_API_KEY"]
    myParams = {'key': gcp_api_key}
    #myHeaders = {'Content-Type': 'application/json'}
    #response = requests.post(gvision_url, headers=myHeaders, params=myParams, json=requestJson)
    response = requests.post(gvision_url, params=myParams, json=requestJson)
    responseCode = response.status_code
    responseHeader = response.headers
    responseJson = response.json()
    print ("Response code: '{}'".format(responseCode))
    print ("Response header: {}".format(responseHeader))
    #printJson(responseJson, "Response JSON")
    if (responseCode == 200):
        with open('landmark-response.json', 'w') as outfile:
            json.dump(responseJson, outfile)
        print("landmark-response.json written!")
        tree = Tree(responseJson)
        try:
            landmarkResponse = {}
            landmarkDescription = tree.execute("$.responses[landmarkAnnotations][0][0].description").encode('utf-8')
            landmarkLocation = tree.execute("$.responses[landmarkAnnotations][0][0].locations[0].latLng")
            print("Landmark Location is: " + json.dumps(landmarkLocation))
            mapUrl = "https://www.google.com/maps/@?api=1&map_action=map&center={},{}&zoom=18&basemap=satellite".format(landmarkLocation["latitude"], landmarkLocation["longitude"])
            landmarkResponse['landmarkDescription']=landmarkDescription
            landmarkResponse['landmarkLocation']=landmarkLocation
            landmarkResponse['landmarkMapUrl']=mapUrl
            landmarkDetected = True
            landmarkResponse['landmarkDetected']=True
            print ("Landmark detected in images is: {}".format(landmarkDescription))
            print ("Landmark map is: {}".format(mapUrl))
        except StopIteration as e:
            print ("******* Response from Google Vision API did not have any landmark")
    return landmarkDetected, landmarkResponse

# def process(image_url):
#     landmark = {}
#     print("############## image_url = {}".format(image_url))
#     imageStr = encodeBytes(getBytes(image_url))
#     detectionType = "LANDMARK_DETECTION"
#     requestJson = {'requests': [{'image': {'content': imageStr}, 'features': [{'type': detectionType}]}]}
#     gvision_url = "https://vision.googleapis.com/v1/images:annotate"
#     gcp_api_key = os.environ["GCP_API_KEY"]
#     myParams = {'key': gcp_api_key}
#     #myHeaders = {'Content-Type': 'application/json'}
#     #response = requests.post(gvision_url, headers=myHeaders, params=myParams, json=requestJson)
#     response = requests.post(gvision_url, params=myParams, json=requestJson)
#     responseCode = response.status_code
#     responseHeader = response.headers
#     responseJson = response.json()
#     print ("Response code: '{}'".format(responseCode))
#     print ("Response header: {}".format(responseHeader))
#     #printJson(responseJson, "Response JSON")
#     if (responseCode == 200):
#         with open('landmark-response.json', 'w') as outfile:
#             json.dump(responseJson, outfile)
#         print("landmark-response.json written!")
#         tree = Tree(responseJson)
#         try:
#             landmarkDescription = tree.execute("$.responses[landmarkAnnotations][0][0].description").encode('utf-8')
#             landmarkLocation = tree.execute("$.responses[landmarkAnnotations][0][0].locations[0].latLng")
#             print("Landmark Location is: " + json.dumps(landmarkLocation))
#             mapUrl = "https://www.google.com/maps/@?api=1&map_action=map&center={},{}&zoom=18&basemap=satellite".format(landmarkLocation["latitude"], landmarkLocation["longitude"])
#             #mapUrl = "https{},{}basemap=satellite".format(landmarkLocation["latitude"], landmarkLocation["longitude"])
#
#             print ("Landmark detected in images is: {}".format(landmarkDescription))
#             print ("Landmark map is: {}".format(mapUrl))
#         except StopIteration as e:
#             print ("******* Response from Google Vision API did not have any landmark")
#     print("Done")
#     return landmark

if __name__ == '__main__':
    url = "https://goo.gl/NrGHLW"
    print "No. of arguments is {}".format(len(sys.argv))
    if len(sys.argv) > 1:
        url = sys.argv[1]
    print(detectLandmark(url))
