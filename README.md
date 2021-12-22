# StarCitizenStoreSniffer
uses python to query RSI's graphql API to monitor and diff results

The parser is rudimentary and being updated to handle certain use cases. The recursive subkey can probably be done more efficiently. 


The chrome cookiefile location is currently hardcoded.

To see VIP(concierge) packages you must use Chrome(currently) to login to the rsi pledge store and then the python query will show you the items your account is eligible for. Its using cookies file and will not ask for your username or password anywhere.  



If you use this please do not query them too fast. Theres no need to query less than the default watchdelay of 25 seconds. There wont be any added benifit. 
