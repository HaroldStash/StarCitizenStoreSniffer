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
parser.add_argument('-u', '--upgrade', help="Show all available upgrades for sale in the store", action="store_true")
parser.add_argument('-s', '--standalone', help="Show all available standalone ships for sale in the store", action="store_true")
parser.add_argument('-a', '--allships', help="Show all ships in the upgrade database", action="store_true")
parser.add_argument('-wd', '--watchdelay', dest='watchdelay', type=int, help='The delay you want to sniff the store at', default=5)
args = parser.parse_args()

api_settoken = "https://robertsspaceindustries.com/api/account/v2/setAuthToken"
api_settokencontext = "https://robertsspaceindustries.com/api/ship-upgrades/setContextToken?fromShipId&pledgeId&toShipId&toSkuId"
api_url_upgrades = "https://robertsspaceindustries.com/pledge-store/api/upgrade/graphql"
api_url_standalone = "https://robertsspaceindustries.com/graphql"
query_upgrades = """query filterShips($fromId: Int, $toId: Int, $fromFilters: [FilterConstraintValues], $toFilters: [FilterConstraintValues]) {
  from(to: $toId, filters: $fromFilters) {
    ships {
      id
      skus {
      id
      title
      price
      upgradePrice
      unlimitedStock
      showStock
      available
      availableStock
      limitedTimeOffer
      body
      items {
        id
        title
      }
      medias {
        storeThumbSkuDetail
      }
    }
    }
  }
  to(from: $fromId, filters: $toFilters) {
    featured {
      reason
      style
      tagLabel
      tagStyle
      footNotes
      shipId
    }
    ships {
      id
skus {
      id
      title
      price
      upgradePrice
      unlimitedStock
      showStock
      available
      availableStock
      limitedTimeOffer
      body
      items {
        id
        title
      }
      medias {
        storeThumbSkuDetail
      }
    }
    }
  }
}

"""
variables_upgrades = """{
  "fromId": 0,
  "fromFilters": [],
  "toFilters": [
    {
      "constraint": "manufacturer",
      "values": []
    },
    {
      "constraint": "prodStatus",
      "values": []
    },
    {
      "constraint": "focus",
      "values": []
    },
    {
      "constraint": "size",
      "values": []
    },
    {
      "constraint": "crewSize",
      "values": []
    }
  ]
}"""
query_standalone="""mutation UpdateCatalogQueryMutation($storeFront: String, $query: SearchQuery!) {
  store(name: $storeFront, browse: true) {
    listing: search(query: $query) {
      resources {
        ...TyItemFragment
        __typename
      }
      __typename
    }
    __typename
  }
}

fragment TyItemFragment on TyItem {
  id
  name
  title
  subtitle
  url
  body
  excerpt
  type
  media {
    thumbnail {
      slideshow
      storeSmall
      __typename
    }
    list {
      slideshow
      __typename
    }
    __typename
  }
  nativePrice {
    amount
    discounted
    discountDescription
    __typename
  }
  price {
    amount
    discounted
    taxDescription
    discountDescription
    __typename
  }
  stock {
    ...TyStockFragment
    __typename
  }
  tags {
    name
    __typename
  }
  ... on TySku {
    label
    customizable
    isWarbond
    isPackage
    isVip
    isDirectCheckout
    __typename
  }
  ... on TyProduct {
    skus {
      id
      isDirectCheckout
      __typename
    }
    isVip
    __typename
  }
  ... on TyBundle {
    isVip
    media {
      thumbnail {
        slideshow
        __typename
      }
      __typename
    }
    discount {
      ...TyDiscountFragment
      __typename
    }
    __typename
  }
  __typename
}

fragment TyDiscountFragment on TyDiscount {
  id
  title
  skus {
    ...TyBundleSkuFragment
    __typename
  }
  products {
    ...TyBundleProductFragment
    __typename
  }
  __typename
}

fragment TyBundleSkuFragment on TySku {
  id
  title
  label
  excerpt
  subtitle
  url
  type
  isWarbond
  isDirectCheckout
  media {
    thumbnail {
      storeSmall
      slideshow
      __typename
    }
    __typename
  }
  gameItems {
    __typename
  }
  stock {
    ...TyStockFragment
    __typename
  }
  price {
    amount
    taxDescription
    __typename
  }
  __typename
}

fragment TyStockFragment on TyStock {
  unlimited
  show
  available
  backOrder
  qty
  backOrderQty
  level
  __typename
}

fragment TyBundleProductFragment on TyProduct {
  id
  name
  title
  subtitle
  url
  type
  excerpt
  stock {
    ...TyStockFragment
    __typename
  }
  media {
    thumbnail {
      storeSmall
      slideshow
      __typename
    }
    __typename
  }
  nativePrice {
    amount
    discounted
    __typename
  }
  price {
    amount
    discounted
    taxDescription
    __typename
  }
  skus {
    ...TyBundleSkuFragment
    __typename
  }
  __typename
}"""
variables_standalone="""{
  "query": {
    "page": 1,
    "sort": {
      "field": "weight",
      "direction": "desc"
    },
    "skus": {
      "products": [
        "72",
        "268",
        "270"
      ]
    },
    "limit": 2500
  }
}
"""
query_allships="""query initShipUpgrade {
  ships {
    id
    name
    focus
    type
    flyableStatus
    owned
    msrp
    link
    skus {
      id
      title
      available
      price
      body
      unlimitedStock
      availableStock
      limitedTimeOffer
    }
  }
}"""
variables_allships="{}"
maxPadHeight = 1000

headers_upgrades = ['name', 'price', 'edition', 'unlimitedStock', 'availableStock', 'limitedTimeOffer']
headers_standalone = ['id', 'name', 'price', 'discount', 'edition', 'unlimitedstock', 'quantity', 'backorder', 'backOrderQty', 'vip']
headers_allships = ['id', 'flyableStatus', 'name', 'price', 'edition', 'unlimitedstock', 'quantity', 'limitedTimeOffer']

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
cookies = browser_cookie3.chrome(cookie_file="C:\\Users\Harold\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Network\\Cookies", domain_name="robertsspaceindustries.com")
#cookies = browser_cookie3.chrome()

#setTokenContext = requests.post(api_settokencontext, cookies=setToken.cookies)
#print(setTokenContext.status_code)
#print(setTokenContext.text)



"""
FUNCTION FOR UPGRADE TABLE
        for i in upgradeJsonData['data']['to']['ships']:
            for j in i['skus']:
                tableData_upgrades.append([j['items'][0]['title'],
                j['price']/100,
                j['title'],
                j['unlimitedStock'],
                j['availableStock'],
                j['limitedTimeOffer']])
                
FUNCTION FOR STANDALONE TABLE
        for i in standaloneJsonData['data']['store']['listing']['resources']:
            tableData_standalone.append([i['id'],
            i['name'],
            i['price']['amount']/100,
            i['price']['discounted'],
            "Warbond Edition" if i['isWarbond'] else "Warbond Edition",
            i['stock']['unlimited'],
            i['stock']['qty'],
            i['stock']['backOrder'],
            i['stock']['backOrderQty'],
            i['isVip']])
FUNCTION FOR ALL SHIPS
            shipIndex = 0
            if allshipsJsonData['data']['ships']:
                for i in allshipsJsonData['data']['ships']:
                    flyableStatus = i['flyableStatus']
                    shipName = i['name']
                    if i['skus'] and len(i['skus']) > 0:
                        skuIndex = 0
                        for j in i['skus']:
                            shipId = j['id']
                            shipPrice = j['price']/100
                            shipEdition = j['title']
                            shipUnlimitedStock = j['unlimitedStock']
                            shipAvailableStock = j['availableStock']
                            shipLimitedTimeOffer = j['limitedTimeOffer']

                            tableData_allships.append([shipId,
                            flyableStatus,
                            shipName,
                            shipPrice,
                            shipEdition,
                            shipUnlimitedStock,
                            shipAvailableStock,
                            shipLimitedTimeOffer])

                            skuIndex += 1

                    elif i['skus'] == None or len(i['skus']) < 1:
                            tableData_allships.append(["None",
                            flyableStatus,
                            shipName,
                            i['msrp']/100,
                            "None",
                            "None",
                            "None",
                            "None"])
                    shipIndex += 1
                    
#table = columnar(tableData_upgrades, headers_upgrades,patterns=patterns, no_borders=False)
#print(table)

        if firstQuery:
            firstQuery = False
            last_standaloneJson = standaloneJsonData
            writeDataFile('standalone', standaloneJsonData['data'])
        if standaloneJsonData['data'] == last_standaloneJson['data']:
            dataMatches = True
        else:
            dataMatches = False
            print("data doesnt match")
            writeDataFile('standalone', standaloneJsonData['data'])
            
"""
def writeDataFile(nametype, data):
    fileName = "data/{}_{}.txt".format(nametype, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    f = open(fileName, "w")
    json.dump(data,f)
    #f.write(data)
    f.close()
    return fileName
    
def queryGraphQLForJson(padlocation, nametype, url, query, variables, cookies):
    query = requests.post(url, json={'query': query, 'variables': variables}, cookies=cookies)
    if query.status_code == 200:
        #print("{} QUERY: PASS {}".format(nametype, query.status_code))
        stdscr.addstr(padlocation, 0, "{} QUERY: PASS {} - {}".format(nametype, query.status_code, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")), curses.color_pair(2) )
    else:
        #print("{} QUERY: FAIL {}".format(nametype, query.status_code))
        stdscr.addstr(padlocation, 0, "{} QUERY: FAIL {} - {}".format(nametype, query.status_code, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")), curses.color_pair(5) )
    return query.json()

def querySetToken():
    query = requests.post(api_settoken, cookies=cookies)
    if query.status_code == 200:
        stdscr.addstr(0, 50, "SET TOKEN: PASS {} - {}".format(query.status_code, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")), curses.color_pair(2))
    else:
        stdscr.addstr(0, 50, "SET TOKEN: FAIL {} - {}".format(query.status_code, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")), curses.color_pair(5))
    #print(query.cookies)
    return query

def doesPreviousJsonEqualCurrent(nametype, previous, current):
    if current['data'] != previous['data']:
        fileName = writeDataFile(nametype, current['data'])
        #print("{} does not match, saving copy. {}".format(nametype, fileName))
        stdscr.addstr(1, 150, "{} does not match, saving copy. {}".format(nametype, fileName), curses.color_pair(5))

def printSeparatorLine():
    lines = ""
    for i in range(40):
        lines = lines + "-"
    print(lines)

def clamp(minvalue, value, maxvalue):
    return max(minvalue, min(value, maxvalue))

def main(stdscr):
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    height, width = stdscr.getmaxyx()
    pad = curses.newpad(maxPadHeight, curses.COLS)
    pad.bkgd(curses.color_pair(3))
    firstQuery = True
    tableData = []
    scrollPosHeight = 0
    scrollPosWidth = 0

    pad.refresh(0, 0, 3, 0, curses.LINES-1,curses.COLS-1)
    stdscr.addstr(height-1, 0, " " * (width - 1), curses.color_pair(1) )
    stdscr.addstr(height-1, 0, "q - to quit ", curses.color_pair(1) )
    stdscr.refresh()
    k = 0
    stdscr.nodelay(1)
    lastTime = 0
    while True:
        if time.time() > lastTime + args.watchdelay:
            setToken = querySetToken()
            json_Upgrade = queryGraphQLForJson(0, "UPGRADE", api_url_upgrades, query_upgrades, variables_upgrades, setToken.cookies)
            json_Standalone = queryGraphQLForJson(1, "STANDALONE", api_url_standalone, query_standalone, variables_standalone, cookies)
            json_Allship = queryGraphQLForJson(2, "ALLSHIPS", api_url_upgrades, query_allships, variables_allships, setToken.cookies)
            if firstQuery:
                firstQuery = False
                previous_json_Upgrade = json_Upgrade
                previous_json_Standalone = json_Standalone
                previous_json_Allship = json_Allship
                writeDataFile("UPGRADE", json_Upgrade['data'])
                writeDataFile("STANDALONE", json_Standalone['data'])
                writeDataFile("ALLSHIPS", json_Allship['data'])
            doesPreviousJsonEqualCurrent("UPGRADE", previous_json_Upgrade, json_Upgrade)
            doesPreviousJsonEqualCurrent("STANDALONE", previous_json_Standalone, json_Standalone)
            doesPreviousJsonEqualCurrent("ALLSHIPS", previous_json_Allship, json_Allship)
############################STANDALONE############################
            if args.standalone:
                for i in json_Standalone['data']['store']['listing']['resources']:
                    tableData.append([i['id'],
                    i['name'],
                    i['price']['amount']/100,
                    i['price']['discounted'],
                    "Warbond Edition" if i['isWarbond'] else "Warbond Edition",
                    i['stock']['unlimited'],
                    i['stock']['qty'],
                    i['stock']['backOrder'],
                    i['stock']['backOrderQty'],
                    i['isVip']])
                table = columnar(tableData, headers_standalone, no_borders=False)
                #print(table)
                tableData = []

                index = 1
                pad.addstr(0, 0, "STANDALONE SHIPS:", curses.COLOR_WHITE)
                for line in table.split('\n'):
                    pad.addstr(index, 0, line, curses.COLOR_WHITE)
                    index += 1
#################################################################
            lastTime = time.time()

        keyPress = stdscr.getch()
        if keyPress == ord('q'):
            break
        elif  keyPress == curses.KEY_DOWN:
            scrollPosHeight = clamp(0, (scrollPosHeight + 1), maxPadHeight-1)
        elif keyPress == curses.KEY_UP:
            scrollPosHeight = clamp(0, (scrollPosHeight - 1), maxPadHeight-1)
        elif  keyPress == curses.KEY_LEFT:
            scrollPosWidth = clamp(0, (scrollPosWidth - 1), curses.COLS-1)
        elif keyPress == curses.KEY_RIGHT:
            scrollPosWidth = clamp(0, (scrollPosWidth + 1), curses.COLS-1)
        pad.refresh(scrollPosHeight, scrollPosWidth, 3, 0, curses.LINES-2,curses.COLS-1)
        stdscr.refresh()
wrapper(main)