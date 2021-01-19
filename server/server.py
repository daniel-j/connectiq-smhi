#!/usr/bin/env python3

from PIL import Image, ImageDraw

import json

import urllib.request
import requests

from osgeo import ogr
from osgeo import osr
import geoio

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse


infoUrl = "https://opendata-download-radar.smhi.se/api/version/latest/area/sweden/product/comp"
# transformUrl = "https://www.lantmateriet.se/api/epi/Transform?type=2&x={x}&y={y}&z=0&id=16461"
#radarTifUrl = "https://opendata-download-radar.smhi.se/api/version/latest/area/sweden/product/comp/latest.tif"
#radarPngUrl = "https://opendata-download-radar.smhi.se/api/version/latest/area/sweden/product/comp/latest.png"
# baseMapUrl = "http://opendata-download-radar.smhi.se/explore/img/basemap.png"
# outlinesUrl = "http://opendata-download-radar.smhi.se/explore/img/outlines.png"

port = 8008

centerx = 0
centery = 0

left = 5983984
down = 126648
right = 7771252
up = 1075693

source = osr.SpatialReference()
source.ImportFromEPSG(4326)
target = osr.SpatialReference()
target.ImportFromEPSG(3006)
transform = osr.CoordinateTransformation(source, target)


def generateImage(lat, lon, scale = 1, screenWidth = 240, screenHeight = 240):

    scaleW = screenWidth / scale
    scaleH = screenHeight / scale

    sizeMin = min(screenWidth, screenHeight)
    sizeMax = max(screenWidth, screenHeight)
    scaleMin = min(scaleW, scaleH)

    radius = sizeMin / scaleMin / 2 # 1 km

    print("WGS84        N " + str(lat) + ", E " + str(lon))
    point = ogr.CreateGeometryFromJson(json.dumps({'type': 'Point', 'coordinates': [lat, lon]}))
    point.Transform(transform)

    [swelat, swelon] = json.loads(point.ExportToJson())['coordinates']
    print("SWEREF 99 TM N " + str(swelat) + ", E " + str(swelon))

    print("Fetching " + infoUrl)
    info = requests.get(url=infoUrl).json()['lastFiles'][0]
    for fmt in info['formats']:
        if fmt['key'] == 'png':
            radarPngUrl = fmt['link']
        elif fmt['key'] == 'tif':
            radarTifUrl = fmt['link']

    urllib.request.urlretrieve(radarTifUrl, "/tmp/smhi-radar-latest.tif")
    with geoio.GeoImage("/tmp/smhi-radar-latest.tif") as geoImg:
        (centerx, centery) = geoImg.proj_to_raster(swelon,swelat)
        print("Raster coords:", (centerx, centery))

    def drawCircle(drawim, x, y, radius, color, width=1):
        drawim.arc([(x - radius, y - radius), (x + radius, y + radius)], 0, 360, fill=color, width=width)

    with Image.open("assets/basemap.png") as basemap:
        with Image.open("assets/outlines.png") as outlines:
            print("Fetching " + radarPngUrl)
            with Image.open(requests.get(url=radarPngUrl, stream=True).raw) as im:

                width = im.width
                height = im.height
                
                newImage = Image.new("RGBA", (width, height), (255, 255, 255, 0))

                newImage.paste(basemap, (0, 0), basemap)
                newImage.paste(outlines, (0, 0), outlines)
                newImage.paste(im, (0, 0), im)

                box = (centerx - scaleW / 2, centery - scaleH / 2, centerx + scaleW / 2, centery + scaleH / 2)
                croppedImage = newImage.crop(box)
                newImage = Image.new("RGB", croppedImage.size, "#ccc")
                newImage.paste(croppedImage, (0, 0), croppedImage)
                newImage = newImage.resize((screenWidth, screenHeight), Image.NEAREST)

                overlayImg = Image.new("RGBA", (screenWidth, screenHeight), (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlayImg)
                drawCircle(draw, screenWidth / 2, screenHeight / 2, 1, "#C00")
                drawCircle(draw, screenWidth / 2, screenHeight / 2, radius*10, "#F00")
                drawCircle(draw, screenWidth / 2, screenHeight / 2, radius*30, "#F90")
                drawCircle(draw, screenWidth / 2, screenHeight / 2, radius*50, "#0D0")
                overlayImg = overlayImg.resize((screenWidth, screenHeight), Image.LANCZOS)

                newImage.paste(overlayImg, (0, 0), overlayImg)

    return newImage


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        info = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(info.query)
        if info.path == '/radar':
            print(info, query)
            
            #self.wfile.write(bytes("<html><head><title>Title goes here.</title></head>", "utf-8"))
            #self.wfile.write(bytes("<body><p>This is a test.</p>", "utf-8"))
            #self.wfile.write(bytes("<p>You accessed path: %s</p>" % self.path, "utf-8"))
            #self.wfile.write(bytes("</body></html>", "utf-8"))
            img = generateImage(float(query['lat'][0]), float(query['lon'][0]), int(query['scale'][0]), int(query['screenWidth'][0]), int(query['screenHeight'][0]))
            self.send_response(200)
            self.send_header("Content-type", "image/gif")
            self.end_headers()
            img.save(self.wfile, "GIF")
            #img.show()
        else:
            print("Unknown path: " + self.path)


if __name__ == "__main__":
    httpd = HTTPServer(('', port), Server)

    #img = generateImage(57.719599, 11.993140, 4, 240, 240)
    #img.show()
    
    print('Starting http server on port %d...' % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
