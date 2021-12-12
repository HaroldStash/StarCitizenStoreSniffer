import json
import argparse
import time
from termcolor import colored
import requests
from columnar import columnar
from click import style
import datetime

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
        "72"
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
variables_allships=""""""

headers_upgrades = ['name', 'price', 'edition', 'unlimitedStock', 'availableStock', 'limitedTimeOffer']
tableData_upgrades = []

headers_standalone = ['id', 'name', 'price', 'discount', 'edition', 'unlimitedstock', 'quantity', 'backorder', 'backOrderQty']
tableData_standalone = []

headers_allships = ['id', 'flyableStatus', 'name', 'price', 'edition', 'unlimitedstock', 'quantity', 'limitedTimeOffer']
tableData_allships = []

last_allshipsJson = {'data'}
dataMatches = True
firstQuery = True

patterns = [
    ('True', lambda text: style(text, fg='white', bg='green')),
    ('False', lambda text: style(text, fg='white', bg='red')),
    ('None', lambda text: style(text, fg='black', bg='white')),
    ('Warbond', lambda text: style(text, fg='white', bg='yellow')),
    ('.+Upgrade', lambda text: style(text, fg='white', bg='blue')),
    ('<<.+', lambda text: style(text, fg='white', bg='magenta'))
]

setToken = requests.post(api_settoken)
if setToken.status_code == 200:
    print("SET TOKEN: PASS")
else:
    print("SET TOKEN ERROR: {}".format(setToken.status_code))
#print(setToken.cookies)

#setTokenContext = requests.post(api_settokencontext)
#print(setTokenContext.status_code)
#print(setTokenContext.text)


def writeDataFile(filetype, data):
    f = open("data/{}_{}.txt".format(filetype, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")), "w")
    json.dump(data,f)
    #f.write(data)
    f.close()

while True:
    if args.upgrade:
        queryUpgradeSystem = requests.post(api_url_upgrades, json={'query': query_upgrades, 'variables': variables_upgrades}, cookies=setToken.cookies)
        if queryUpgradeSystem.status_code == 200:
            print("UPGRADE QUERY: PASS")
        else:
            print("UPGRADE QUERY: {}".format(queryUpgradeSystem.status_code))
        upgradeJsonData = queryUpgradeSystem.json()
        for i in upgradeJsonData['data']['to']['ships']:
            for j in i['skus']:
                tableData_upgrades.append([j['items'][0]['title'],
                j['price']/100,
                j['title'],
                j['unlimitedStock'],
                j['availableStock'],
                j['limitedTimeOffer']])
        table = columnar(tableData_upgrades, headers_upgrades,patterns=patterns, no_borders=False)
        print(table)
    if args.standalone:
        queryStandalone = requests.post(api_url_standalone, json={'query': query_standalone, 'variables': variables_standalone}, cookies=setToken.cookies)
        if queryStandalone.status_code == 200:
            print("STANDALONE QUERY: PASS")
        else:
            print("STANDALONE QUERY: {}".format(queryStandalone.status_code))
        standaloneJsonData = queryStandalone.json()
        for i in standaloneJsonData['data']['store']['listing']['resources']:
            tableData_standalone.append([i['id'],
            i['name'],
            i['price']['amount']/100,
            i['price']['discounted'],
            "Warbond" if i['isWarbond'] else "Standard",
            i['stock']['unlimited'],
            i['stock']['qty'],
            i['stock']['backOrder'],
            i['stock']['backOrderQty']])
        table = columnar(tableData_standalone, headers_standalone,patterns=patterns, no_borders=False)
        print(table)
    if args.allships:
        queryAllShips = requests.post(api_url_upgrades, json={'query': query_allships}, cookies=setToken.cookies)
        if queryAllShips.status_code == 200:
            print("ALLSHIPS QUERY: PASS")
        else:
            print("ALLSHIPS QUERY: {}".format(queryAllShips.status_code))
        allshipsJsonData = queryAllShips.json()
        if firstQuery:
            firstQuery = False
            last_allshipsJson = allshipsJsonData
            writeDataFile('allships', allshipsJsonData['data'])
        if allshipsJsonData['data']:
            if allshipsJsonData['data'] == last_allshipsJson['data']:
                dataMatches = True
            else:
                dataMatches = False
                print("data doesnt match")
                writeDataFile('allships', allshipsJsonData['data'])
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
                table = columnar(tableData_allships, headers_allships ,patterns=patterns, no_borders=False)
                print(table)
                tableData_allships = []
                last_allshipsJson = allshipsJsonData
            else:
                print("There were no ships returned {}".format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
        else:
            print("There was no 'data' returned {}".format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))

    
    time.sleep(args.watchdelay)