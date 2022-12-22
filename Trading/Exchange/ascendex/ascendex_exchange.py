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
import octobot_trading.exchanges.connectors.ccxt.exchange_settings_ccxt as exchange_settings_ccxt


class AscendExConnectorSettings(exchange_settings_ccxt.CCXTExchangeConfig):
    @classmethod
    def set_connector_settings(cls, exchange_connector):
        cls.GET_MY_RECENT_TRADES_METHODS = [
            exchange_connector.get_my_recent_trades_using_closed_orders.__name__,
        ]
        cls.MARKET_STATUS_PARSER.FIX_PRECISION = True
        cls.CANDLE_LOADING_LIMIT = 500
        


class AscendEx(exchanges.SpotCCXTExchange):
    CONNECTOR_CONFIG_CLASS = AscendExConnectorSettings

    DESCRIPTION = ""

    BUY_STR = "Buy"
    SELL_STR = "Sell"

    ACCOUNTS = {
        trading_enums.AccountTypes.CASH: 'cash',
        trading_enums.AccountTypes.MARGIN: 'margin',
        trading_enums.AccountTypes.FUTURE: 'futures',  # currently in beta
    }

    @classmethod
    def get_name(cls):
        return 'ascendex'

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return cls.get_name() == exchange_candidate_name

    async def switch_to_account(self, account_type):
        # TODO
        pass
