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

import octobot_trading.exchanges as exchanges
import octobot_trading.exchanges.connectors.ccxt.exchange_settings_ccxt \
    as exchange_settings_ccxt


class GateIOConnectorSettings(
    exchange_settings_ccxt.CCXTExchangeConfig):
    @classmethod
    def set_connector_settings(cls, exchange_connector):
        cls.MARKET_STATUS_PARSER.FIX_PRECISION = True
        cls.MAX_RECENT_TRADES_PAGINATION_LIMIT = 100
        cls.MAX_ORDERS_PAGINATION_LIMIT = 100
        cls.MARKET_STATUS_PARSER.REMOVE_INVALID_PRICE_LIMITS = True


class GateIO(exchanges.SpotCCXTExchange):
    CONNECTOR_CONFIG_CLASS = GateIOConnectorSettings

    @classmethod
    def get_name(cls):
        return "gateio"

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return exchange_candidate_name == cls.get_name()
