import json
import argparse
import time
from termcolor import colored
import requests
from columnar import columnar

parser = argparse.ArgumentParser(description='RSI Store Parser')
#parser.add_argument('-u', '--upgrades', help="Show all available upgrades", action="store_true")
parser.add_argument('-wd', '--watchdelay', dest='watchdelay', type=int, help='The delay you want to sniff the store at', default=10)
args = parser.parse_args()

api_settoken = "https://robertsspaceindustries.com/api/account/v2/setAuthToken"
api_settokencontext = "https://robertsspaceindustries.com/api/ship-upgrades/setContextToken?fromShipId&pledgeId&toShipId&toSkuId"
api_url = "https://robertsspaceindustries.com/pledge-store/api/upgrade/graphql"
filterShips = """query filterShips($fromId: Int, $toId: Int, $fromFilters: [FilterConstraintValues], $toFilters: [FilterConstraintValues]) {
  from(to: $toId, filters: $fromFilters) {
    ships {
      id
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
variables = """{
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

setToken = requests.post(api_settoken)
if setToken.status_code is 200:
    print("SET TOKEN: PASS")
else:
    print("SET TOKEN ERROR: {}".format(setToken.status_code))
#print(setToken.cookies)

#setTokenContext = requests.post(api_settokencontext)
#print(setTokenContext.status_code)
#print(setTokenContext.text)

while True:
    queryUpgradeSystem = requests.post(api_url, json={'query': filterShips, 'variables': variables}, cookies=setToken.cookies)
    if queryUpgradeSystem.status_code is 200:
        print("UPGRADE QUERY: PASS")
    else:
        print("UPGRADE QUERY: {}".format(queryUpgradeSystem.status_code))
    #print(queryUpgradeSystem.text)

    data = queryUpgradeSystem.json()
    for i in data['data']['to']['ships']:
        print("{}\n-${}".format(colored(i['skus'][0]['items'][0]['title'], "yellow"), i['skus'][0]['price']/100))
    print(len(data['data']['to']['ships']))
    time.sleep(args.watchdelay)