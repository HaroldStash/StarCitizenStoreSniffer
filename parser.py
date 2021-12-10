import json
import argparse
import time
from termcolor import colored
import requests
from columnar import columnar
from click import style

parser = argparse.ArgumentParser(description='RSI Store Parser')
parser.add_argument('-u', '--upgrade', help="Show all available upgrades", action="store_true")
parser.add_argument('-s', '--standalone', help="Show all available standalone ships", action="store_true")
parser.add_argument('-wd', '--watchdelay', dest='watchdelay', type=int, help='The delay you want to sniff the store at', default=10)
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
query_standalone="""query GetBrowseListingQuery($storeFront: String, $query: SearchQuery) {
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
    "skus": {
      "products": [
        "72"
      ]
    },
    "limit": 2500,
    "page": 1,
    "sort": {
      "field": "weight",
      "direction": "desc"
    }
  },
  "storeFront": "pledge"
}
"""

headers_upgrades = ['name', 'price', 'edition', 'unlimitedStock', 'availableStock', 'limitedTimeOffer']
tableData_upgrades = []
headers_standalone = ['id', 'name', 'price', 'edition', 'unlimitedstock', 'quantity', 'backorder', 'backOrderQty']
tableData_standalone = []
storedJsonData = 0

patterns = [
    ('True', lambda text: style(text, fg='white', bg='green')),
    ('False', lambda text: style(text, fg='white', bg='red')),
    ('Warbond', lambda text: style(text, fg='white', bg='yellow')),
    ('.+Upgrade', lambda text: style(text, fg='white', bg='blue'))
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

while True:
    if args.upgrade:
        queryUpgradeSystem = requests.post(api_url_upgrades, json={'query': query_upgrades, 'variables': variables_upgrades}, cookies=setToken.cookies)
        if queryUpgradeSystem.status_code == 200:
            print("UPGRADE QUERY: PASS")
        else:
            print("UPGRADE QUERY: {}".format(queryUpgradeSystem.status_code))
        jsonData = queryUpgradeSystem.json()
        for i in jsonData['data']['to']['ships']:
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
        jsonData = queryStandalone.json()#headers_standalone = ['id', 'name', 'price', 'edition', 'unlimitedstock', 'quantity', 'backorder', 'backOrderQty']
        for i in jsonData['data']['store']['listing']['resources']:
            tableData_standalone.append([i['id'],
            i['name'],
            i['price']['amount']/100,
            "Warbond" if i['isWarbond'] else "Standard",
            i['stock']['unlimited'],
            i['stock']['qty'],
            i['stock']['backOrder'],
            i['stock']['backOrderQty']])
        table = columnar(tableData_standalone, headers_standalone,patterns=patterns, no_borders=False)
        print(table)


    
    time.sleep(args.watchdelay)