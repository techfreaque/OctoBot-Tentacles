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
import decimal
import typing
import ccxt

import octobot_trading.enums as trading_enums
import octobot_trading.exchanges as exchanges
import octobot_trading.constants as constants
import octobot_trading.exchanges.connectors.ccxt.exchange_settings_ccxt_generic as exchange_settings_ccxt_generic
import octobot_commons.constants as commons_constants
import octobot_trading.exchanges.connectors.exchange_test_status as exchange_test_status


class BybitConnectorSettings(exchange_settings_ccxt_generic.GenericCCXTExchangeConfig):
    is_fully_tested = exchange_test_status.ExchangeTestStatus(
        is_fully_tested=True
    )
    only_futures_is_tested = exchange_test_status.ExchangeTestStatus(
        futures_real_tested=True, futures_testnet_tested=True
    )
    # test status
    MARKET_STATUS_PARSER_TEST_STATUS = is_fully_tested
    ORDERS_PARSER_TEST_STATUS = is_fully_tested
    TRADES_PARSER_TEST_STATUS = is_fully_tested
    POSITIONS_PARSER_TEST_STATUS = is_fully_tested
    TICKER_PARSER_TEST_STATUS = is_fully_tested

    CANDLE_LOADING_LIMIT_TEST_STATUS = is_fully_tested
    MAX_RECENT_TRADES_PAGINATION_LIMIT_TEST_STATUS = is_fully_tested
    MAX_ORDER_PAGINATION_LIMIT_TEST_STATUS = is_fully_tested
    GET_ORDER_METHODS_TEST_STATUS = only_futures_is_tested
    GET_ALL_ORDERS_METHODS_TEST_STATUS = only_futures_is_tested
    GET_OPEN_ORDERS_METHODS_TEST_STATUS = only_futures_is_tested
    GET_CLOSED_ORDERS_METHODS_TEST_STATUS = only_futures_is_tested
    CANCEL_ORDERS_METHODS_TEST_STATUS = only_futures_is_tested
    GET_MY_RECENT_TRADES_METHODS_TEST_STATUS = only_futures_is_tested
    GET_POSITIONS_METHODS_TEST_STATUS = is_fully_tested
    GET_POSITION_METHODS_TEST_STATUS = is_fully_tested

    @classmethod
    def set_connector_settings(cls, exchange_connector):
        cls.MARKET_STATUS_PARSER.FIX_PRECISION = True
        cls.POSITIONS_PARSER.MODE_KEYS = ["positionIdx", "mode"]
        cls.POSITIONS_PARSER.ONEWAY_VALUES = ["MergedSingle", "0"]
        cls.POSITIONS_PARSER.HEDGE_VALUES = ["BothSide", "1", "2"]
        cls.ORDERS_PARSER.TEST_AND_FIX_SPOT_QUANTITIES = True
        cls.FUNDING_RATE_PARSER.FUNDING_TIME_UPDATE_PERIOD = (
            8 * commons_constants.HOURS_TO_SECONDS
        )
        cls.CANDLE_LOADING_LIMIT = 200
        cls.MARK_PRICE_IN_TICKER = True
        cls.MARK_PRICE_IN_POSITION = False
        cls.FUNDING_IN_TICKER = True
        cls.ADD_COST_TO_CREATE_SPOT_MARKET_ORDER = True
        
        cls.GET_POSITION_CONFIG: typing.List[dict] = [
            # {"settleCoin": "USDT", "dataFilter": "full"},
            ]
        cls.GET_POSITIONS_CONFIG: typing.List[dict] = [
            {"subType": "linear", "settleCoin": "USDT", "dataFilter": "full"},
            # {"subType": "linear", "settleCoin": "USDC", "dataFilter": "full"},
            {"subType": "inverse", "settleCoin": "BTC", "dataFilter": "full"},
            {"subType": "inverse", "settleCoin": "ETH", "dataFilter": "full"},
            {"subType": "inverse", "settleCoin": "EOS", "dataFilter": "full"},
            {"subType": "inverse", "settleCoin": "XRP", "dataFilter": "full"},
            {"subType": "inverse", "settleCoin": "DOT", "dataFilter": "full"},
            {"subType": "inverse", "settleCoin": "BIT", "dataFilter": "full"},
            {"subType": "inverse", "settleCoin": "ADA", "dataFilter": "full"},
            {"subType": "inverse", "settleCoin": "MANA", "dataFilter": "full"},
            {"subType": "inverse", "settleCoin": "LTC", "dataFilter": "full"},
            {"subType": "option"},
            {"subType": "swap"},
        ]


class Bybit(exchanges.SpotCCXTExchange, exchanges.FutureCCXTExchange):
    CONNECTOR_CONFIG_CLASS = BybitConnectorSettings

    DESCRIPTION = ""

    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        if exchange_manager.is_future:
            # Bybit default take profits are market orders
            # note: use BUY_MARKET and SELL_MARKET since in reality those are conditional market orders, which behave the same
            # way as limit order but with higher fees
            _BYBIT_BUNDLED_ORDERS = [
                trading_enums.TraderOrderType.STOP_LOSS,
                trading_enums.TraderOrderType.BUY_MARKET,
                trading_enums.TraderOrderType.SELL_MARKET,
            ]
            self.SUPPORTED_BUNDLED_ORDERS = {
                trading_enums.TraderOrderType.BUY_MARKET: _BYBIT_BUNDLED_ORDERS,
                trading_enums.TraderOrderType.SELL_MARKET: _BYBIT_BUNDLED_ORDERS,
                trading_enums.TraderOrderType.BUY_LIMIT: _BYBIT_BUNDLED_ORDERS,
                trading_enums.TraderOrderType.SELL_LIMIT: _BYBIT_BUNDLED_ORDERS,
            }

    BUY_STR = "Buy"
    SELL_STR = "Sell"

    LONG_STR = BUY_STR
    SHORT_STR = SELL_STR

    # Position
    BYBIT_BANKRUPTCY_PRICE = "bustPrice"
    BYBIT_CLOSING_FEE = "occClosingFee"
    BYBIT_MODE = "positionIdx"
    BYBIT_REALIZED_PNL = "RealisedPnl"

    # Funding
    BYBIT_DEFAULT_FUNDING_TIME = 8 * commons_constants.HOURS_TO_SECONDS

    # Orders
    BYBIT_REDUCE_ONLY = "reduceOnly"
    BYBIT_TRIGGER_ABOVE_KEY = "triggerDirection"
    BYBIT_TRIGGER_ABOVE_VALUE = "1"

    @classmethod
    def get_name(cls) -> str:
        return "bybit"

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return cls.get_name() == exchange_candidate_name

    def get_default_type(self):
        if self.exchange_manager.is_future:
            return 'linear'
        return 'spot'

    async def create_market_stop_loss_order(
        self, symbol, quantity, price, side, current_price, params=None
    ) -> dict:
        params = params or {}
        if self.exchange_manager.is_future:
            params["triggerPrice"] = price
            # Trigger the order when market price rises to triggerPrice or falls to triggerPrice. 1: rise; 2: fall
            params["triggerDirection"] = 1 if price > current_price else 2
        elif self.exchange_manager.is_spot_only:
            # see https://bybit-exchange.github.io/docs/spot/v3/#t-placeactive
            params["orderCategory"] = 1
            params["triggerPrice"] = price
        order = await self.connector.client.create_order(symbol, "market", side, quantity, params=params)
        return order
    
    def custom_get_order_stop_params(self, order_id, params)->dict:
        if self.exchange_manager.is_future:
            params["stop"] = True
        elif self.exchange_manager.is_spot_only:
            # see https://bybit-exchange.github.io/docs/spot/v3/#t-getactive
            params["orderCategory"] = 1
        return params

    def custom_get_all_orders_stop_params(self, params) -> dict:
        if self.exchange_manager.is_future:
            if "stop" not in params:
                # only fetch untriggered stop orders
                params["stop"] = True
        elif self.exchange_manager.is_spot_only:
            # see https://bybit-exchange.github.io/docs/spot/v3/#t-openorders
            params["orderCategory"] = 1
        return params

    def custom_get_open_orders_stop_params(self, params) -> dict:
        return self.custom_get_all_orders_stop_params(params)

    def custom_get_closed_orders_stop_params(self, params) -> dict:
        return self.custom_get_all_orders_stop_params(params)

    def custom_edit_stop_orders_params(self, order_id, stop_price, params) -> dict:
        if self.exchange_manager.is_future:
            params["stop_order_id"] = order_id
            if stop_price is not None:
                # params["stop_px"] = stop_price
                # params["stop_loss"] = stop_price
                params["triggerPrice"] = str(stop_price)
        return params
    
    def custom_cancel_stop_orders_params(self, order_id, params) -> dict:
        # from bybit docs: You may cancel all untriggered conditional orders or take profit/stop loss order.
        # Essentially, after a conditional order is triggered, it will become an active order. So, when a conditional
        # order is triggered, cancellation has to be done through the active order endpoint for any unfilled or
        # partially filled active order
        params["stop_order_id"] = order_id
        return params
    

    async def set_symbol_partial_take_profit_stop_loss(self, symbol: str, inverse: bool,
                                                       tp_sl_mode: trading_enums.TakeProfitStopLossMode):
        # /contract/v3/private/position/switch-tpsl-mode
        # from https://bybit-exchange.github.io/docs/derivativesV3/contract/#t-dv_switchpositionmode
        params = {
            "symbol": self.connector.client.market(symbol)['id'],
            "tpSlMode": tp_sl_mode.value
        }
        try:
            await self.connector.client.privatePostContractV3PrivatePositionSwitchTpslMode(params)
        except ccxt.ExchangeError as e:
            if "same tp sl mode1" in str(e):
                # can't fetch the tp sl mode1 value
                return
            raise

    def get_order_additional_params(self, order) -> dict:
        params = {}
        if self.exchange_manager.is_future:
            contract = self.exchange_manager.exchange.get_pair_future_contract(order.symbol)
            params["positionIdx"] = self._get_position_idx(contract)
            params["reduceOnly"] = order.reduce_only
        return params


    def get_bundled_order_parameters(self, stop_loss_price=None, take_profit_price=None) -> dict:
        """
        Returns True when this exchange supports orders created upon other orders fill (ex: a stop loss created at
        the same time as a buy order)
        :param stop_loss_price: the bundled order stopLoss price
        :param take_profit_price: the bundled order takeProfit price
        :return: A dict with the necessary parameters to create the bundled order on exchange alongside the
        base order in one request
        """
        params = {}
        if stop_loss_price is not None:
            params["stopLoss"] = str(stop_loss_price)
        if take_profit_price is not None:
            params["takeProfit"] = str(take_profit_price)
        return params

    def _get_position_idx(self, contract):
        # "position_idx" has to be set when trading futures
        # from https://bybit-exchange.github.io/docs/inverse/#t-myposition
        # Position idx, used to identify positions in different position modes:
        # 0-One-Way Mode
        # 1-Buy side of both side mode
        # 2-Sell side of both side mode
        if contract.is_one_way_position_mode():
            return 0
        else:
            raise NotImplementedError(
                f"Hedge mode is not implemented yet. Please switch to One-Way position mode from the Bybit "
                f"trading interface preferences of {contract.pair}"
            )
            # TODO
            # if Buy side of both side mode:
            #     return 1
            # else Buy side of both side mode:
            #     return 2

    def parse_mark_price(self, mark_price_dict, from_ticker=False) -> dict:
        if from_ticker and constants.CCXT_INFO in mark_price_dict:
            try:
                return {
                    trading_enums.ExchangeConstantsMarkPriceColumns.MARK_PRICE.value:
                        mark_price_dict[constants.CCXT_INFO][trading_enums.ExchangeConstantsMarkPriceColumns.MARK_PRICE.value]
                }
            except KeyError:
                pass
        try:
            mark_price_dict = {
                trading_enums.ExchangeConstantsMarkPriceColumns.MARK_PRICE.value:
                    decimal.Decimal(mark_price_dict[
                        trading_enums.ExchangeConstantsTickersColumns.CLOSE.value])
            }
        except KeyError as e:
            # do not fill mark price with 0 when missing as might liquidate positions
            self.logger.error(f"Fail to parse mark price dict ({e})")

        return mark_price_dict
