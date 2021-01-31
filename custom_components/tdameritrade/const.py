"""Constants for the TDAmeritrade integration."""

DOMAIN = "tdameritrade"

TITLE = "TDAmeritrade"

OAUTH2_AUTHORIZE = "https://auth.tdameritrade.com/auth"
OAUTH2_TOKEN = "https://api.tdameritrade.com/v1/oauth2/token"
TDA_URL = "https://api.tdameritrade.com/v1"


CONF_CONSUMER_KEY = "consumer_key"
CONF_ACCOUNTS = "accounts"

# API const
CLIENT = "client"
PRE_MARKET = "preMarket"
POST_MARKET = "postMarket"
REG_MARKET = "regularMarket"
EQUITY = "equity"
EQ = "EQ"
SECURITIES_ACCOUNT = "securitiesAccount"
TYPE = "type"
CASH_AVAILABLE_FOR_TRADEING = "cashAvailableForTrading"
CURRENT_BALANCES = "currentBalances"
AVAILABLE_FUNDS = "availableFunds"
MARGIN = "MARGIN"
CASH = "CASH"
SESSION_HOURS = "sessionHours"
START = "start"
END = "end"
IS_OPEN = "isOpen"
EQUITY_MKT_TYPE = "EQUITY"

OPEN_SCAN_INTERVAL = 10
CLOSED_SCAN_INTERVAL = 300
