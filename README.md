# hass-tdameritrade
TDAmeritrade component for Home Assistant

# Requirements
In order to use this component, you must register for a [devloper](https://developer.tdameritrade.com/) account with TDAmeritrade.

Once registered add a new app.  Ensure that you configure the callback URL as such. 

```https://localhost:8123/auth/external/callback```

Note: The callback URL must be https, http is not supported.

# Installation
Clone the repo and copy the tdameritrade folder to custom_components or use [HACS](https://github.com/hacs/integration)

#Configuration

Add the following to configuration.yaml

```
tdameritrade:
  consumer_key: YOUR CONSUMER KEY
```

In the UI select Configuration > Integrations > Add.

In the list choose TDAmeritrade.

You will be prompted to authenticate with TDAmeritrade, this requests and offline token and will be good for 90 days.

Once authenticated, select the TDAmeritrade integration and select settings.

Add your accounts as a comma seperated list and then click save.

Restart Home Assistant.

The component will create a binary sensor for the regular market hours and a sensor for each account.

# Supported Services

## Get a quote 
tdameritrade.get_quote
```
data:
  symbol: SPMD
```

This will create an entitiy in the following form get_quote_service.spmd, with the market price as the value.

## Place an order
tdameritrade.place_order
```
data:
  price: 10
  instruction: BUY
  quantity: 5
  symbol: SPMD
  account_id: 012344567
  order_type: LIMIT
  session: NORMAL
  duration: DAY
  orderStrategyType: SINGLE
  assetType: EQUITY
```


# Example automation

```
alias: Place order for SPMD in Roth IRA 
description: Buy SPMD with all available funds in Roth account
trigger:
- at: 09:45:00
  platform: time
condition:
- condition: state
  entity_id: binary_sensor.market
  state: 'on'
action:
  service: homeassistant.turn_on 
  entity_id: script.buy_stock_ira
  data_template:
    variables:
      ticker: SPMD 
      account: "{{ states.sensor.available_funds_0218.attributes.accountId }}"  
      av_funds: "{{ states.sensor.available_funds_0218.state }}"
```

# Example Script

```
alias: Roth Autotrade                                                                                    
sequence:                                                                                                
- data_template:
    symbol: "{{ ticker }}"
  service: tdameritrade.get_quote                                                                        
- condition: template
  value_template: "{{ ((av_funds | float) // (states.get_quote_service[ticker|lower].attributes.bidPrice | float)) > 0 }}"
- data_template:
    account_id: "{{ account }}"
    assetType: EQUITY
    duration: DAY
    instruction: BUY
    orderStrategyType: SINGLE
    order_type: LIMIT
    price: "{{ states.get_quote_service[ticker|lower].attributes.bidPrice }}"
    quantity: "{{ ((av_funds | float) // (states.get_quote_service[ticker|lower].attributes.bidPrice | float)) }}"
    session: NORMAL
    symbol: "{{ ticker }}"
  service: tdameritrade.place_order
- data_template:
    message: "Placed order for {{ ((av_funds | float) // (states.get_quote_service[ticker|lower].attributes.bidPrice | float)) }} shares of {{ ticker }} at {{ sttes.get_quote_service[ticker|lower].attributes.bidPrice }} in account {{ account }}." 
    title: "TDAmeritrade - Order Placed" 
  service: notify.pushbullet
```
