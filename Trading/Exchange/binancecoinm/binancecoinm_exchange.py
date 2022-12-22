#  Drakkar-Software OctoBot-Tentacles
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.

import octobot_trading.enums as trading_enums
import octobot_trading.exchanges as exchanges
from octobot_trading.exchanges.connectors.ccxt import exchange_settings_ccxt
from octobot_commons import constants as commons_constants
from octobot_trading.exchanges.connectors import exchange_settings
import tentacles.Trading.Exchange.binance.binance_exchange as binance_exchange


class BinanceCoinMConnectorConfig(binance_exchange.BinanceConnectorConfig):
    @classmethod
    def set_connector_settings(cls, exchange_connector):
        cls.MARK_PRICE_IN_POSITION = True
        cls.FUNDING_RATE_PARSER.FUNDING_TIME_UPDATE_PERIOD = (
            8 * commons_constants.HOURS_TO_SECONDS
            )
        cls.ORDER_NOT_FOUND_SETS_THE_ORDER_TO_CANCELED: bool = True

    
class BinanceCoinM(binance_exchange.Binance):  
    CONNECTOR_CONFIG_CLASS: exchange_settings.ExchangeConfig = BinanceCoinMConnectorConfig
    DESCRIPTION = ""

    ACCOUNTS = {
        trading_enums.AccountTypes.FUTURE: 'future'
    }


    BINANCE_SYMBOL = "symbol"

    BINANCE_FUTURE_UNREALIZED_PNL = "unRealizedProfit"
    BINANCE_FUTURE_LIQUIDATION_PRICE = "liquidationPrice"
    BINANCE_FUTURE_VALUE = "liquidationPrice"

    BINANCE_MARGIN_TYPE = "marginType"
    BINANCE_MARGIN_TYPE_ISOLATED = "ISOLATED"
    BINANCE_MARGIN_TYPE_CROSSED = "CROSSED"



    BINANCE_TIME = "time"
    BINANCE_MARK_PRICE = "markPrice"
    BINANCE_ENTRY_PRICE = "entryPrice"

    @classmethod
    def get_name(cls):
        return 'binancecoinm'

    async def get_funding_rate_history(self, symbol: str, limit: int = 100, **kwargs: dict) -> list:
        return [
            self.parse_funding_rate(funding_rate_dict)
            for funding_rate_dict in (await self.connector.client.fapiPublic_get_fundingrate(
                {self.BINANCE_SYMBOL: self.get_exchange_pair(symbol),
                 "limit": limit}))
        ]

    async def set_symbol_leverage(self, symbol: str, leverage: int, **kwargs: dict):
        await self.connector.client.fapiPrivate_post_leverage(
            {self.BINANCE_SYMBOL: self.get_exchange_pair(symbol),
             "leverage": leverage})

    async def set_symbol_margin_type(self, symbol: str, isolated: bool):
        await self.connector.client.fapiPrivate_post_marginType(
            {
                self.BINANCE_SYMBOL: self.get_exchange_pair(symbol),
                self.BINANCE_MARGIN_TYPE: self.BINANCE_MARGIN_TYPE_ISOLATED
                if isolated else self.BINANCE_MARGIN_TYPE_CROSSED
            })


    def parse_mark_price(self, mark_price_dict, from_ticker=False):
        try:
            mark_price_dict = {
                trading_enums.ExchangeConstantsMarkPriceColumns.MARK_PRICE.value:
                    self.connector.client.safe_float(mark_price_dict, self.BINANCE_MARK_PRICE, 0)
            }
        except KeyError as e:
            self.logger.error(f"Fail to parse mark_price dict ({e})")
        return mark_price_dict
