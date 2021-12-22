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

parser = argparse.ArgumentParser(description='RSI Store Sniffer')
parser.add_argument('-wd', '--watchdelay', dest='watchdelay', type=int, help='The delay you want to sniff the store at', default=25)
args = parser.parse_args()

api_settoken = "https://robertsspaceindustries.com/api/account/v2/setAuthToken"
api_settokencontext = "https://robertsspaceindustries.com/api/ship-upgrades/setContextToken?fromShipId&pledgeId&toShipId&toSkuId"
api_url_upgrades = "https://robertsspaceindustries.com/pledge-store/api/upgrade/graphql"
api_url_standalone = "https://robertsspaceindustries.com/graphql"

query_allships="""mutation UpdateCatalogQueryMutation($storeFront: String, $query: SearchQuery!) {
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
variables_allships="""{
  "query": {
    "skus": {
      "products": [
        "2"
      ]
    },
    "limit": 10000,
    "page": 1,
    "sort": {
      "field": "weight",
      "direction": "desc"
    }
  },
  "storeFront": "pledge"
}"""
maxPadHeight = 2500

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

cookies = browser_cookie3.chrome(cookie_file="C:\\Users\Harold\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Network\\Cookies", domain_name="robertsspaceindustries.com")

def writeDataFile(nametype, data):
    fileName = "checker/{}_{}.txt".format(nametype, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    f = open(fileName, "w")
    json.dump(data,f)
    #f.write(data)
    f.close()
    return fileName
    
def queryGraphQLForJson(checkindex, url, query, variablesorig, cookies):
    variables_json = json.loads(variablesorig)
    variables_json['query']['skus']['products'] = checkIndex
    query = requests.post(url, json={'query': query, 'variables': json.dumps(variables_json)}, cookies=cookies)
    if query.status_code == 200:
        return query.json()
    else:
        return {}


def querySetToken():
    query = requests.post(api_settoken, cookies=cookies)
    if query.status_code == 200:
        stdscr.addstr(0, 50, "SET TOKEN: PASS {} - {}".format(query.status_code, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")), curses.color_pair(2))
    else:
        stdscr.addstr(0, 50, "SET TOKEN: FAIL {} - {}".format(query.status_code, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")), curses.color_pair(5))
    #print(query.cookies)
    return query

def clamp(minvalue, value, maxvalue):
    return max(minvalue, min(value, maxvalue))

checkIndex = -985
lastTime = 0

while True:
    if time.time() > lastTime + args.watchdelay:
        jsonFromRequest = queryGraphQLForJson(checkIndex, api_url_standalone, query_allships, variables_allships, cookies)
        writeDataFile("LISTING_{}".format(checkIndex), jsonFromRequest)
        print(checkIndex)
        checkIndex += 1
        lastTime = time.time()
