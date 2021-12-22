import json
import argparse
import time
from termcolor import colored
import requests
from columnar import columnar
from click import style
import datetime
import browser_cookie3
import curses
from curses import wrapper
import os
import random

parser = argparse.ArgumentParser(description='RSI Store Parser')
#parser.add_argument('-wd', '--watchdelay', dest='watchdelay', type=int, help='The delay you want to sniff the store at', default=25)
args = parser.parse_args()


maxPadHeight = 2500
maxPadWidth = 2500
currentPadIndex = 0
pad = []

headers_upgrades = ['sku', 'name', 'price', 'extras', 'edition', 'unlimitedStock', 'availableStock', 'limitedTimeOffer']
headers_standalone = ['sku', 'name', 'price', 'discount', 'edition', 'unlimitedstock', 'quantity', 'backorder', 'backOrderQty', 'vip']
headers_allships = ['id', 'sku', 'flyableStatus', 'name', 'price', 'edition', 'unlimitedstock', 'quantity', 'limitedTimeOffer']

previous_json_Upgrade = {'data'}
previous_json_Allship = {'data'}
previous_json_Standalone = {'data'}

patterns = [
    ('True', lambda text: style(text, fg='white', bg='green')),
    ('False', lambda text: style(text, fg='white', bg='red')),
    ('None', lambda text: style(text, fg='black', bg='white')),
    ('.+Warbond', lambda text: style(text, fg='white', bg='yellow')),
    ('.+Upgrade', lambda text: style(text, fg='white', bg='blue')),
    ('.+Paint', lambda text: style(text, fg='white', bg='magenta'))
]

stdscr = curses.initscr()



def clamp(minvalue, value, maxvalue):
    return max(minvalue, min(value, maxvalue))

def addToPad(data, color, result = False):
    global currentPadIndex
    padColumn = 0
    if result:
        padColumn = 2
    pad.addstr(currentPadIndex, padColumn, data, color)
    currentPadIndex += 1
    pad.refresh(0, 0, 3, 0, curses.LINES-2, curses.COLS-1)

def findItemById(resourceID, itemList):
    result = False
    for item in itemList:
        if item['id'] == resourceID:
            result = item
    return result

def getDifferences(fileType, baseFile, changedFile):
    print("baseFile    {}".format(baseFile))
    print("changedFile {}".format(changedFile))
    with open(baseFile) as fileContent:
        baseFileJson = json.load(fileContent)
    with open(changedFile) as fileContent:
        changedFileJson = json.load(fileContent)

    jsonBaseItems = []
    jsonChangedItems = []
    if fileType == 0:
        jsonBaseItems = baseFileJson['data']['store']['listing']['resources']
        jsonChangedItems = changedFileJson['data']['store']['listing']['resources']
    if fileType == 1:
        jsonBaseItems = baseFileJson['data']['ships']
        jsonChangedItems = changedFileJson['data']['ships']
    if fileType == 2:
        jsonBaseItems = baseFileJson['data']['to']['ships']
        jsonChangedItems = changedFileJson['data']['to']['ships']

    addToPad("Base:    {}".format(baseFile), curses.COLOR_WHITE)
    addToPad("Changed: {}".format(changedFile), curses.COLOR_WHITE)
    baseResourceCount = len(jsonBaseItems)
    changedFileCount = len(jsonChangedItems)

    for changedResource in jsonChangedItems:
        resourceInBase = findItemById(changedResource['id'], jsonBaseItems)
        if resourceInBase == False:
            for baseResource in jsonBaseItems:
                resourceInChanged = findItemById(baseResource['id'], jsonChangedItems)
                if resourceInChanged == False and changedResource['name'] == baseResource['name']:
                    addToPad("   Resource ID changed: {} to {}".format(baseResource['id'], changedResource['id']), curses.color_pair(6))
        else:
            if resourceInBase != changedResource:
                itemName = ""
                if fileType == 0:
                    itemName = changedResource['name']
                    itemId = changedResource['id']
                if fileType == 1:
                    itemName = changedResource['name']
                    itemId = changedResource['id']
                if fileType == 2:
                    itemName = changedResource['skus'][0]['items'][0]['title']
                    itemId = changedResource['skus'][0]['id']
                addToPad("Changes to item: [{}] id: {}".format(itemName, itemId), curses.color_pair(7))
                for key in changedResource:
                    if changedResource[key] != resourceInBase[key]:
                        if type(changedResource[key]) == str:
                            addToPad("   Property Changed: key: [{}] - current: [{}] previous: [{}]".format(key, changedResource[key], resourceInBase[key]), curses.color_pair(7))
                        else:
                            subKeyIndex = 0
                            for subKey in changedResource[key]:
                                if type(subKey) == str:
                                    if changedResource[key][subKey] != resourceInBase[key][subKey]:
                                        addToPad("   SubProperty Changed: parent: [{}] key: [{}] - current: [{}] previous: [{}]".format(key, subKey, changedResource[key][subKey], resourceInBase[key][subKey]), curses.color_pair(7))
                                else:
                                    for subSubKey in subKey:
                                        if type(subSubKey) == str:
                                            if subKeyIndex < len(resourceInBase[key]):
                                                if subKey[subSubKey] != resourceInBase[key][subKeyIndex][subSubKey]:
                                                    addToPad("   subKeyIndex:{} ".format(subKeyIndex), curses.color_pair(7))
                                                    addToPad("     Parent Changed: [{}] key: [{}] current: [{}] previous: [{}]".format(key, subSubKey, subKey[subSubKey], resourceInBase[key][subKeyIndex][subSubKey]), curses.color_pair(7))
                                            else:
                                                addToPad("   Added new subKeyIndex:{} to [{}] key:[{}] value:[{}]".format(subKeyIndex, key, subSubKey, subKey[subSubKey]), curses.color_pair(7))
                                subKeyIndex += 1

    for resource in jsonBaseItems:
        if findItemById(resource['id'], jsonChangedItems) == False:
            addToPad("   Resource Removed: [{}] {}".format(resource['id'], resource['name']), curses.color_pair(5))

    for resource in jsonChangedItems:
        if findItemById(resource['id'], jsonBaseItems) == False:
            resourceName = ""
            resourcePrice = ""
            if fileType == 0:
                resourceName = resource['name']
                resourcePrice = resource['nativePrice']['amount']/100
            if fileType == 1:
                resourceName = resource['name']
                resourcePrice = resource['msrp']/100
            if fileType == 2:
                #resourceName = resource['skus'][0]['title']
                resourceName = resource['skus'][0]['items'][0]['title']
                resourcePrice = resource['skus'][0]['price']/100
            addToPad("   Resource Added: [{}] ${} {}".format(resource['id'], resourcePrice, resourceName), curses.color_pair(2))

    addToPad("", curses.COLOR_WHITE)



def main(stdscr):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)
    height, width = stdscr.getmaxyx()
    global pad
    pad = curses.newpad(maxPadHeight, maxPadWidth)
    pad.bkgd(curses.color_pair(3))
    firstQuery = True
    tableData = []
    scrollPosHeight = 0
    scrollPosWidth = 0


    stdscr.addstr(height-1, 0, " " * (width - 1), curses.color_pair(1) )
    stdscr.addstr(height-1, 0, " q - to quit", curses.color_pair(1) )
    stdscr.nodelay(False)
    lastTime = 0

    #listOfFiles = os.listdir('./data')
    listOfFiles = [os.path.abspath(os.path.join('./data',i)) for i in os.listdir('./data')]
    standAloneFiles = []
    allShipsFiles = []
    upgradeFiles = []
    for file in listOfFiles:
        if "STANDALONE" in file:
            standAloneFiles.append(file)
        if "ALLSHIPS" in file:
            allShipsFiles.append(file)
        if "UPGRADE" in file:
            upgradeFiles.append(file)
    stdscr.addstr(0, 0, "STANDALONE Files: {}".format(len(standAloneFiles)), curses.color_pair(2))
    stdscr.addstr(1, 0, "ALLSHIPS Files: {}".format(len(allShipsFiles)), curses.color_pair(2))
    stdscr.addstr(2, 0, "UPGRADE Files: {}".format(len(upgradeFiles)), curses.color_pair(2))
    fileArray = [standAloneFiles, allShipsFiles, upgradeFiles]

    for setOfFiles in fileArray:
        if len(setOfFiles) > 1:
            print(setOfFiles)
            fileIndex = 0
            if "STANDALONE" in setOfFiles[0]:
                addToPad("###########STANDALONE DIFFERENCES###########", curses.COLOR_WHITE, False)
                fileType = 0
            elif "ALLSHIPS" in setOfFiles[0]:
                addToPad("###########ALLSHIPS DIFFERENCES###########", curses.COLOR_WHITE, False)
                fileType = 1
            elif "UPGRADE" in setOfFiles[0]:
                addToPad("###########UPGRADE DIFFERENCES###########", curses.COLOR_WHITE, False)
                fileType = 2
            for file in setOfFiles:
                if fileIndex == 0:
                    baseFileCompare = file
                else:
                    changedFileToCompare = file
                    getDifferences(fileType, baseFileCompare, changedFileToCompare)
                    baseFileCompare = file
                fileIndex += 1
            addToPad("#########################################", curses.COLOR_WHITE, False)

    while True:
        #if time.time() > lastTime + args.watchdelay:

            #lastTime = time.time()

        keyPress = stdscr.getch()
        if keyPress == ord('q'):
            break
        elif  keyPress == curses.KEY_DOWN:
            scrollPosHeight = clamp(0, (scrollPosHeight + 1), maxPadHeight-1)
        elif keyPress == curses.KEY_UP:
            scrollPosHeight = clamp(0, (scrollPosHeight - 1), maxPadHeight-1)
        elif  keyPress == curses.KEY_NPAGE:
            scrollPosHeight = clamp(0, (scrollPosHeight + 45), maxPadHeight-1)
        elif keyPress == curses.KEY_PPAGE:
            scrollPosHeight = clamp(0, (scrollPosHeight - 45), maxPadHeight-1)
        elif  keyPress == curses.KEY_LEFT:
            scrollPosWidth = clamp(0, (scrollPosWidth - 1), maxPadWidth-1)
        elif keyPress == curses.KEY_RIGHT:
            scrollPosWidth = clamp(0, (scrollPosWidth + 1), maxPadWidth-1)
        pad.refresh(scrollPosHeight, scrollPosWidth, 3, 0, curses.LINES-2, curses.COLS-1)
        #=stdscr.refresh()
wrapper(main)