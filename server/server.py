#!/usr/bin/env python3

from datetime import datetime, timedelta

from PIL import Image, ImageDraw, ImageFont
import os
import json

import urllib.request
import requests

from osgeo import ogr
from osgeo import osr
import geoio

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

from staticmap import StaticMap, CircleMarker
import math

apiBaseUrl = 'https://opendata-download-radar.smhi.se'

infoUrl = apiBaseUrl + '/api/version/latest/area/sweden/product/comp'
dayUrl = apiBaseUrl + '/api/version/latest/area/sweden/product/comp/{year}/{month}/{day}'
# transformUrl = "https://www.lantmateriet.se/api/epi/Transform?type=2&x={x}&y={y}&z=0&id=16461"
#radarTifUrl = "https://opendata-download-radar.smhi.se/api/version/latest/area/sweden/product/comp/latest.tif"
#radarPngUrl = "https://opendata-download-radar.smhi.se/api/version/latest/area/sweden/product/comp/latest.png"
# baseMapUrl = "http://opendata-download-radar.smhi.se/explore/img/basemap.png"
# outlinesUrl = "http://opendata-download-radar.smhi.se/explore/img/outlines.png"

basemap = Image.open("assets/basemap.png")
outlines = Image.open("assets/outlines.png")

port = 8008

font = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 14)

source = osr.SpatialReference()
source.ImportFromEPSG(4326)
target = osr.SpatialReference()
target.ImportFromEPSG(3006)
transform = osr.CoordinateTransformation(source, target)

def drawCircle(drawim, x, y, radius, color, width=1):
    drawim.arc([(x - radius, y - radius), (x + radius, y + radius)], 0, 360, fill=color, width=width)

def drawCenteredText(drawim, text, width, y, fill="black", font=font):
    h = 0
    for msg in text.split('\n'):
        (textw, texth) = drawim.textsize(msg, font=font)
        drawim.text((width / 2 - textw / 2, y + h), msg, font=font, fill=fill)
        h += texth + 2

cache = {}

def fetchDay(delta = 0):
    date = datetime.utcnow() + timedelta(delta)
    url = dayUrl.format(year=date.strftime('%Y'), month=date.strftime('%m'), day=date.strftime('%d'))
    print("Fetching date ", url)
    info = requests.get(url=url).json()
    return info

def getHistory(count = 6):
    files = fetchDay(0)['files']
    if len(files) < count:
        files = fetchDay(-1)['files'] + files
    return files[-count:]

def cacheFile(item, formats=['png', 'tif']):
    item['valid_dt'] = datetime.strptime(item['valid'], '%Y-%m-%d %H:%M')
    for fmt in item['formats']:
        if fmt['key'] in formats:
            url = fmt['link']
            print("Downloading " + url)
            if fmt['key'] == 'png':
                fmt['image'] = Image.open(requests.get(url=url, stream=True).raw)
            elif fmt['key'] == 'tif':
                urllib.request.urlretrieve(url, "/tmp/smhi-radar.tif")
                fmt['geoimg'] = geoio.GeoImage("/tmp/smhi-radar.tif")
                os.remove("/tmp/smhi-radar.tif")
    cache[item['key']] = item

def cleanCache(count = 6):
    itemsToDelete = list(cache.values())
    if count > 0:
        itemsToDelete = itemsToDelete[:-count]
    for item in itemsToDelete:
        print(">> Deleting " + item['key'])
        for fmt in item['formats']:
            if 'image' in fmt:
                fmt['image'].close()
        cache.pop(item['key'])

def updateCache(count=6):
    files = getHistory(count) # 6 = 30 minutes back
    for item in files:
        if item['key'] not in cache:
            print("Adding " + item['key'] + ' to cache')
            try:
                cacheFile(item)
            except Exception as e:
                print("Unable to add " + item['key'] + ' to cache: ', e)
    cleanCache(count)


def generateImage(item, lat, lon, zoom = 7, screenWidth = 240, screenHeight = 240, pretty=False):

    tileSize = 256
    C = 40075.016686 # in km
    Stile = C * math.cos(math.radians(lat)) / (2 ** zoom)
    Spixel = tileSize / Stile


    print("WGS84        N " + str(lat) + ", E " + str(lon))
    point = ogr.CreateGeometryFromJson(json.dumps({'type': 'Point', 'coordinates': [lat, lon]}))
    point.Transform(transform)
    [swelat, swelon] = json.loads(point.ExportToJson())['coordinates']
    print("SWEREF 99 TM N " + str(swelat) + ", E " + str(swelon))

    for fmt in item['formats']:
        if fmt['key'] == 'png':
            radarPngImg = fmt['image']
        elif fmt['key'] == 'tif':
            radarTifGeoImg = fmt['geoimg']

    (centerx, centery) = radarTifGeoImg.proj_to_raster(swelon,swelat)
    print("Raster coords:", (centerx, centery))

    im = radarPngImg
    width = im.width
    height = im.height

    if pretty:
        m = StaticMap(screenWidth, screenHeight, 0, 0, "http://a.tile.osm.org/{z}/{x}/{y}.png", tileSize)
        marker = CircleMarker((lon, lat), "#F00", 0)
        m.add_marker(marker)
        newImage = m.render(zoom=int(zoom))
    else:
        newImage = Image.new("RGB", (screenWidth, screenHeight), "#AAA")

    

    radarLayer = Image.new("RGBA", (width, height))
    if not pretty:
        radarLayer.paste(basemap, (0, 0))
        radarLayer.paste(outlines, (0, 0), outlines)
    radarLayer.paste(im, (0, 0), im)

    scale = Spixel * 2 # 1 px = 2 km
    scaleW = screenWidth / scale
    scaleH = screenHeight / scale


    sizeMin = min(screenWidth, screenHeight)
    sizeMax = max(screenWidth, screenHeight)
    scaleMin = min(scaleW, scaleH)
    radius = sizeMin / scaleMin / 2

    x = math.floor(centerx - scaleW / 2)
    y = math.floor(centery - scaleH / 2)
    w = math.ceil(scaleW) + 1
    h = math.ceil(scaleH) + 1

    resX = -math.floor(((centerx - scaleW / 2) % 1) * scale)
    resY = -math.floor(((centery - scaleH / 2) % 1) * scale)
    resWidth = math.floor(w * scale)
    resHeight = math.floor(h * scale)

    box = (x, y, x + w, y + h)

    radarLayer = radarLayer.crop(box)
    radarLayer = radarLayer.resize((resWidth, resHeight), Image.NEAREST)
    newImage.paste(radarLayer, (resX, resY), radarLayer)

    draw = ImageDraw.Draw(newImage)
    drawCircle(draw, screenWidth / 2, screenHeight / 2, radius*1, "#C00")
    drawCircle(draw, screenWidth / 2, screenHeight / 2, radius*10, "#F00")
    drawCircle(draw, screenWidth / 2, screenHeight / 2, radius*30, "#F90")
    drawCircle(draw, screenWidth / 2, screenHeight / 2, radius*50, "#0C0")
    drawCircle(draw, screenWidth / 2, screenHeight / 2, radius*70, "#00F")
    print(item['valid'])
    totalMinute, second = divmod((datetime.utcnow() - item['valid_dt']).seconds, 60)
    hour, minute = divmod(totalMinute, 60)
    drawCenteredText(draw, str(minute) + " min ago", screenWidth, screenHeight - 40)

    return newImage


class Server(BaseHTTPRequestHandler):
    def do_GET(self):
        info = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(info.query)
        if info.path == '/radar':
            print(info, query)
            position = int(query['position'][0]) if 'position' in query else 0
            pretty = 'pretty' in query and int(query['pretty'][0]) == 1

            updateCache(1)

            item = list(cache.values())[position - 1]
            img = generateImage(item, float(query['lat'][0]), float(query['lon'][0]), float(query['scale'][0]), int(query['screenWidth'][0]), int(query['screenHeight'][0]), pretty)

            self.send_response(200)
            self.send_header("Content-type", "image/png")
            self.end_headers()
            img.save(self.wfile, "PNG", quality=100, lossless=True)
            #img.show()
        else:
            self.send_response(404)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Not found.</title></head>", "utf-8"))
            self.wfile.write(bytes("<body><p>404 Not found.</p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
            
            print("Unknown path: " + self.path)


if __name__ == "__main__":
    httpd = HTTPServer(('', port), Server)
    
    print('Starting http server on port %d...' % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
