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

def findResourceById(resourceID, fileJson):
    result = False
    for resource in fileJson['data']['store']['listing']['resources']:
        if resource['id'] == resourceID:
            result = resource
    return result

def getDifferences(baseFile, changedFile):
    print("baseFile    {}".format(baseFile))
    print("changedFile {}".format(changedFile))
    with open(baseFile) as fileContent:
        baseFileJson = json.load(fileContent)
    with open(changedFile) as fileContent:
        changedFileJson = json.load(fileContent)
#STANDALONE FILE
    if baseFileJson['data']:
        if 'store' in baseFileJson['data']:
            resourceIndex = 0
            addToPad("Base:    {}".format(baseFile), curses.COLOR_WHITE)
            addToPad("Changed: {}".format(changedFile), curses.COLOR_WHITE)
            baseResourceCount = len(baseFileJson['data']['store']['listing']['resources'])
            changedFileCount = len(changedFileJson['data']['store']['listing']['resources'])

            for resource in changedFileJson['data']['store']['listing']['resources']:
                resourceObject = findResourceById(resource['id'], baseFileJson)
                if resourceObject == False:
                    for subResource in baseFileJson['data']['store']['listing']['resources']:
                        subResourceObject = findResourceById(subResource['id'], changedFileJson)
                        if subResourceObject == False and resource['name'] == subResource['name']:
                            addToPad("Resource ID changed: {} to {}".format(subResource['id'], resource['id']), curses.COLOR_WHITE, True)

            if changedFileCount < baseResourceCount:
                for resource in baseFileJson['data']['store']['listing']['resources']:
                    if findResourceById(resource['id'], changedFileJson) == False:
                        addToPad("Resource Removed: {}".format(resource['id']), curses.COLOR_WHITE, True)
            else:
                for resource in changedFileJson['data']['store']['listing']['resources']:
                    if findResourceById(resource['id'], baseFileJson) == False:
                        addToPad("Resource Added: [{}] {}".format(resource['id'], resource['name']), curses.COLOR_WHITE, True)

            #for baseResource in baseFileJson['data']['store']['listing']['resources']:
            #    changedResource = findResourceById(baseResource['id'], changedFileJson)
            #    if changedResource:
            #        if baseResource != changedResource:
            #            addToPad("Updated ID: {}".format(baseResource['id']), curses.COLOR_WHITE, True)
            #            ##LIST OUT OTHER CHANGES HERE


            resourceIndex += 1
    #elif baseFile['data']['from']['ships']:#UPGRADE FILE
        #DO UPGRADE STUFF
    #elif baseFile['data']['ships']:#ALLSHIPS FILE
        #DO ALLSHIPS STUFF

def main(stdscr):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    height, width = stdscr.getmaxyx()
    global pad
    pad = curses.newpad(maxPadHeight, curses.COLS)
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
            elif "ALLSHIPS" in setOfFiles[0]:
                addToPad("###########ALLSHIPS DIFFERENCES###########", curses.COLOR_WHITE, False)
            elif "UPGRADE" in setOfFiles[0]:
                addToPad("###########UPGRADE DIFFERENCES###########", curses.COLOR_WHITE, False)
            for file in setOfFiles:
                if fileIndex == 0:
                    baseFileCompare = file
                else:
                    changedFileToCompare = file
                    getDifferences(baseFileCompare, changedFileToCompare)
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
            scrollPosWidth = clamp(0, (scrollPosWidth - 1), curses.COLS-1)
        elif keyPress == curses.KEY_RIGHT:
            scrollPosWidth = clamp(0, (scrollPosWidth + 1), curses.COLS-1)
        pad.refresh(scrollPosHeight, scrollPosWidth, 3, 0, curses.LINES-2, curses.COLS-1)
        #=stdscr.refresh()
wrapper(main)