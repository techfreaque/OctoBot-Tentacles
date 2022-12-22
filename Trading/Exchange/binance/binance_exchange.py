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


class BinanceConnectorConfig(exchange_settings_ccxt.CCXTExchangeConfig):
    @classmethod
    def set_connector_settings(cls, exchange_connector):
        cls.MARK_PRICE_IN_POSITION = True
        cls.FUNDING_RATE_PARSER.FUNDING_TIME_UPDATE_PERIOD = (
            8 * commons_constants.HOURS_TO_SECONDS
        )
        cls.ORDER_NOT_FOUND_SETS_THE_ORDER_TO_CANCELED: bool = True


class Binance(exchanges.SpotCCXTExchange):
    CONNECTOR_CONFIG_CLASS = BinanceConnectorConfig
    DESCRIPTION = ""

    BUY_STR = "BUY"
    SELL_STR = "SELL"

    ACCOUNTS = {
        trading_enums.AccountTypes.CASH: 'cash'
    }

    BINANCE_MARK_PRICE = "markPrice"


    @classmethod
    def get_name(cls):
        return 'binance'

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return cls.get_name() == exchange_candidate_name

    async def get_balance(self, **kwargs):
        return await exchanges.SpotCCXTExchange.get_balance(self, **self._get_params(kwargs))

    def _get_params(self, params):
        if params is None:
            params = {}
        params.update({'recvWindow': 60000})
        return params

    async def create_market_stop_loss_order(
        self, symbol, quantity, price, side, current_price, params=None
    ) -> dict:
        order_type = None
        try:
            if (
                trading_enums.TradeOrderType.STOP_LOSS.value.upper()
                in self.connector.client.markets[symbol][
                    trading_enums.ExchangeOrderCCXTColumns.INFO.value
                ]["orderTypes"]
            ):
                order_type = trading_enums.TradeOrderType.STOP_LOSS.value
        except KeyError:
            # this should never happen as markets should be alreday initialized
            raise RuntimeError(
                f"failed to create market stop order, market status is not loaded"
            )
        if not order_type:
            order_type = trading_enums.TradeOrderType.STOP_LOSS_LIMIT.value
            self.logger.warning(
                "OctoBot will use a STOP LOSS LIMIT ORDER istead of a market stop loss. "
                "Make sure you understand the risk of a STOP LOSS LIMIT ORDER in practice, "
                "as the order might never be filled when the trigger price is reached! - "
                f"MARKET STOP LOSS ORDERS ARE NOT SUPPORTED WITH {symbol} - "
            )
        return await self.connector.client.create_stop_order(
            symbol,
            order_type,
            side,
            quantity,
            price,
            stopPrice=price,
            params=params,
        )
