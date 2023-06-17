import contextlib
import decimal
import time

import ccxt.async_support as ccxt
import typing

import octobot_commons.constants
import octobot_commons.enums
import octobot_commons.symbols as commons_symbols

import octobot_trading
import octobot_trading.constants as constants
import octobot_trading.enums as enums
import octobot_trading.errors
import octobot_trading.exchanges as exchanges
from octobot_trading.exchanges.connectors.ccxt.ccxt_connector import CCXTConnector
import octobot_trading.personal_data as personal_data
from octobot_trading.enums import (
    ExchangeConstantsOrderColumns as ecoc,
    OrderStatus,
)
from tentacles.Trading.Exchange.ibkr.connector.ibkr_client import IBKREchangeClient


class IBKRExchangeConnector(CCXTConnector):
    """
    IBKR library connector
    """

    def __init__(
        self,
        config,
        exchange_manager,
        adapter_class=None,
        additional_config=None,
        rest_name=None,
        force_auth=False,
    ):
        super().__init__(config, exchange_manager)

    def _create_client(self):
        self.client: IBKREchangeClient = IBKREchangeClient()
        self.is_authenticated = True
        self._connect_client()

    # async def initialize_impl(self):
    #     if self.exchange_manager.exchange.is_supporting_sandbox():
    #         self.set_sandbox_mode(self.exchange_manager.is_sandboxed)

    #     await self._ensure_auth()

    #     with self.error_describer():
    #         await self.client.load_markets()

    #     # initialize symbols and timeframes
    #     self.symbols = self.get_client_symbols()
    #     self.time_frames = self.get_client_time_frames()

    # def get_client_symbols(self):
    #     return (
    #         set(self.client.symbols)
    #         if hasattr(self.client, "symbols") and self.client.symbols is not None
    #         else set()
    #     )

    # def get_client_time_frames(self):
    #     return set(self.client.timeframes)

    # @classmethod
    # def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
    #     return isinstance(exchange_candidate_name, str)

    def _create_exchange_type(self):
        self.exchange_type = self.exchange_manager.exchange_class_string

    # def get_ccxt_client_login_options(self):
    #     """
    #     :return: ccxt client login option dict, can be overwritten to custom exchange login
    #     """
    #     if self.exchange_manager.is_future:
    #         return {"defaultType": "future"}
    #     if self.exchange_manager.is_margin:
    #         return {"defaultType": "margin"}
    #     return {"defaultType": "spot"}

    # def add_headers(self, headers_dict):
    #     """
    #     Add new headers to ccxt client
    #     :param headers_dict: the additional header keys and values as dict
    #     """
    #     for header_key, header_value in headers_dict.items():
    #         self.headers[header_key] = header_value
    #         if self.client is not None:
    #             self.client.headers[header_key] = header_value

    # def add_options(self, options_dict):
    #     """
    #     Add new options to ccxt client
    #     :param options_dict: the additional option keys and values as dict
    #     """
    #     for option_key, option_value in options_dict.items():
    #         self.options[option_key] = option_value
    #         if self.client is not None:
    #             self.client.options[option_key] = option_value

    # async def _ensure_auth(self):
    #     try:
    #         await self.get_balance()
    #     except Exception as error:
    #         raise (f"Error when checking exchange connection: {error}") from error

    def _connect_client(self):
        """
        Exchange instance creation
        :return:
        """
        try:
            self.client.connect("127.0.0.1", 4001, 123)
            # self.client.run()

        except Exception as error:
            self.logger.exception(
                error,
                True,
                "configuration issue: IBKR TWS must run on localhost:7497",
            )

    # def use_http_proxy_if_necessary(self):
    #     self.client.aiohttp_trust_env = constants.ENABLE_EXCHANGE_HTTP_PROXY_FROM_ENV

    # def _should_authenticate(self):
    #     return not (self.exchange_manager.is_simulated or
    #                 self.exchange_manager.is_backtesting)

    # def _unauthenticated_exchange_fallback(self, err):
    #     self.is_authenticated = False
    #     self.handle_token_error(err)
    #     self.client = self._get_unauthenticated_exchange()

    # def _get_unauthenticated_exchange(self):
    #     return self.exchange_type(self._get_client_config())

    # def _get_client_config(self, api_key=None, secret=None, password=None):
    #     config = {
    #         'verbose': constants.ENABLE_CCXT_VERBOSE,
    #         'enableRateLimit': constants.ENABLE_CCXT_RATE_LIMIT,
    #         'timeout': constants.DEFAULT_REQUEST_TIMEOUT,
    #         'options': self.options,
    #         'headers': self.headers
    #     }
    #     if api_key is not None:
    #         config['apiKey'] = api_key
    #     if secret is not None:
    #         config['secret'] = secret
    #     if password is not None:
    #         config['password'] = password
    #     # apply self.additional_ccxt_config
    #     config.update(self.additional_ccxt_config or {})
    #     return config

    # def get_market_status(self, symbol, price_example=None, with_fixer=True, ) -> dict:
    #     try:
    #         raw_market_status = self.client.market(symbol)
    #         return self.exchange_manager.exchange.parse_market_status(
    #             raw_market_status=raw_market_status, with_fixer=with_fixer, price_example=price_example)
    #     except ccxt.NotSupported:
    #         raise octobot_trading.errors.NotSupported

    # async def get_balance(self, **kwargs: dict):
    #     """
    #     fetch balance (free + used) by currency
    #     :return: balance dict
    #     """
    #     if not kwargs:
    #         kwargs = {}
    #     try:
    #         with self.error_describer():
    #             balance = await self.client.fetch_balance(params=kwargs)

    #             # remove not currency specific keys
    #             balance.pop(constants.CONFIG_PORTFOLIO_FREE, None)
    #             balance.pop(constants.CONFIG_PORTFOLIO_USED, None)
    #             balance.pop(constants.CONFIG_PORTFOLIO_TOTAL, None)
    #             balance.pop(constants.CCXT_INFO, None)
    #             balance.pop(enums.ExchangeConstantsCCXTColumns.DATETIME.value, None)
    #             balance.pop(enums.ExchangeConstantsCCXTColumns.TIMESTAMP.value, None)
    #             return personal_data.parse_decimal_portfolio(balance)

    #     except ccxt.InvalidNonce as err:
    #         exchanges.log_time_sync_error(self.logger, self.name, err, "real trader portfolio")
    #         raise err
    #     except ccxt.NotSupported:
    #         raise octobot_trading.errors.NotSupported

    # async def get_symbol_prices(
    #     self,
    #     symbol: str,
    #     time_frame: octobot_commons.enums.TimeFrames,
    #     limit: int = None,
    #     since: int = None,
    #     **kwargs: dict,
    # ) -> list:
    #     try:
    #         with self.error_describer():
    #             return await self.client.fetch_ohlcv(
    #                 symbol,
    #                 time_frame.value,
    #                 limit=limit,
    #                 since=since,
    #                 params=kwargs,
    #             )

    #     except Exception as error:
    #         raise octobot_trading.errors.FailedRequest(
    #             f"Failed to get_symbol_prices: Unknown error on {symbol}/{time_frame} {error}"
    #         ) from error

    # async def get_kline_price(
    #     self, symbol: str, time_frame: octobot_commons.enums.TimeFrames, **kwargs: dict
    # ) -> typing.Optional[list]:
    #     try:
    #         # default implementation
    #         return await self.get_symbol_prices(symbol, time_frame, limit=1, **kwargs)
    #     except ccxt.NotSupported:
    #         raise octobot_trading.errors.NotSupported
    #     except ccxt.BaseError as e:
    #         raise octobot_trading.errors.FailedRequest(f"Failed to get_kline_price {e}")

    # # return up to ten bidasks on each side of the order book stack
    # async def get_order_book(
    #     self, symbol: str, limit: int = 5, **kwargs: dict
    # ) -> typing.Optional[dict]:
    #     try:
    #         with self.error_describer():
    #             return await self.client.fetch_order_book(
    #                 symbol, limit=limit, params=kwargs
    #             )
    #     except ccxt.NotSupported:
    #         raise octobot_trading.errors.NotSupported
    #     except ccxt.BaseError as e:
    #         raise octobot_trading.errors.FailedRequest(f"Failed to get_order_book {e}")

    # async def get_recent_trades(
    #     self, symbol: str, limit: int = 50, **kwargs: dict
    # ) -> list:
    #     try:
    #         with self.error_describer():
    #             await self.client.fetchTrades(symbol, limit=limit, params=kwargs)
    #     except ccxt.NotSupported:
    #         raise octobot_trading.errors.NotSupported
    #     except ccxt.BaseError as e:
    #         raise octobot_trading.errors.FailedRequest(
    #             f"Failed to get_recent_trades {e}"
    #         )

    # # A price ticker contains statistics for a particular market/symbol for some period of time in recent past (24h)
    # async def get_price_ticker(
    #     self, symbol: str, **kwargs: dict
    # ) -> typing.Optional[dict]:
    #     try:
    #         with self.error_describer():
    #             raw_ticker = await self.client.fetch_ticker(symbol, params=kwargs)
    #         return await self.exchange_manager.exchange.parse_ticker(
    #             raw_ticker=raw_ticker, symbol=symbol
    #         )
    #     except ccxt.NotSupported:
    #         raise octobot_trading.errors.NotSupported
    #     except ccxt.BaseError as e:
    #         raise octobot_trading.errors.FailedRequest(
    #             f"Failed to get_price_ticker {e}"
    #         )

    # async def get_all_currencies_price_ticker(self, **kwargs: dict) -> list:
    #     try:
    #         with self.error_describer():
    #             symbols = kwargs.pop("symbols", None)
    #             self.all_currencies_price_ticker = (
    #                 await self.exchange_manager.exchange.parse_tickers(
    #                     await self.client.fetch_tickers(symbols, params=kwargs)
    #                 )
    #             )
    #         return self.all_currencies_price_ticker
    #     except ccxt.NotSupported:
    #         raise octobot_trading.errors.NotSupported
    #     except ccxt.BaseError as e:
    #         raise octobot_trading.errors.FailedRequest(
    #             f"Failed to get_all_currencies_price_ticker {e}"
    #         )

    # async def get_order(
    #     self,
    #     order_id: str,
    #     symbol: str = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> typing.Optional[dict]:
    #     defined_methods = self.connector_config.GET_ORDER_METHODS
    #     if self.get_order_default.__name__ in defined_methods and (
    #         order := await self.get_order_default(
    #             order_id, symbol, check_completeness=check_completeness, **kwargs
    #         )
    #     ):
    #         return order
    #     if self.get_order_from_open_and_closed_orders.__name__ in defined_methods and (
    #         order := await self.get_order_from_open_and_closed_orders(
    #             order_id, symbol, check_completeness=check_completeness, **kwargs
    #         )
    #     ):
    #         return order
    #     if self.get_order_using_stop_params.__name__ in defined_methods and (
    #         order := await self.get_order_using_stop_params(
    #             order_id, symbol, check_completeness=check_completeness
    #         )
    #     ):
    #         return order
    #     if self.get_trade.__name__ in defined_methods and (
    #         order := await self.get_trade(
    #             order_id, symbol, check_completeness=check_completeness
    #         )
    #     ):
    #         return order
    #     self.logger.debug(
    #         f"Order not found using get_order: {order_id} / {symbol} - order might not exist anymore"
    #     )

    # async def get_order_default(
    #     self,
    #     order_id: str,
    #     symbol: str = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> typing.Optional[dict]:
    #     if self.client.has.get("fetchOrder"):
    #         try:
    #             with self.error_describer():
    #                 params = kwargs.pop("params", {})
    #                 if order := await self.client.fetch_order(
    #                     order_id, symbol, params=params
    #                 ):
    #                     await self.exchange_manager.exchange.parse_order(
    #                         order, check_completeness=check_completeness
    #                     )
    #         except ccxt.OrderNotFound:
    #             # some exchanges are throwing this error when an order is cancelled (ex: coinbase pro)
    #             pass
    #         except ccxt.NotSupported as e:
    #             self.logger.exception(
    #                 e,
    #                 True,
    #                 "Failed to fetch order using get_order_default: Not Supported",
    #             )
    #         except Exception as e:
    #             self.logger.exception(
    #                 e, True, "Failed to fetch order using get_order_default"
    #             )
    #     return None

    # async def get_order_using_stop_params(
    #     self,
    #     order_id: str,
    #     symbol: str = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> typing.Optional[dict]:
    #     if self.client.has.get("fetchOrder"):
    #         try:
    #             with self.error_describer():
    #                 params = kwargs.pop("params", {})
    #                 if params := self.exchange_manager.exchange.custom_get_order_stop_params(
    #                     order_id, params
    #                 ):
    #                     if order := await self.client.fetch_order(
    #                         order_id, symbol, params=params
    #                     ):
    #                         return await self.exchange_manager.exchange.parse_order(
    #                             order, check_completeness=check_completeness
    #                         )
    #         except ccxt.OrderNotFound:
    #             # some exchanges are throwing this error when an order is cancelled
    #             pass
    #         except Exception as e:
    #             self.logger.exception(
    #                 e, True, "Failed to get order using get_order_using_stop_params"
    #             )
    #     return None

    # async def get_order_from_open_and_closed_orders(
    #     self,
    #     order_id: str,
    #     symbol: str = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> typing.Optional[dict]:
    #     for order in await self.get_open_orders(
    #         symbol, check_completeness=check_completeness, **kwargs
    #     ):
    #         if order[ecoc.ID.value] == order_id:
    #             return order
    #     for order in await self.get_closed_orders(
    #         symbol, check_completeness=check_completeness, **kwargs
    #     ):
    #         if order[ecoc.ID.value] == order_id:
    #             return order
    #     return None  # OrderNotFound

    # async def get_all_orders(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> list:
    #     limit = self.cut_order_pagination_limit(limit)
    #     defined_methods = self.connector_config.GET_ALL_ORDERS_METHODS
    #     orders = []
    #     if self.get_all_orders_default.__name__ in defined_methods:
    #         orders += await self.get_all_orders_default(
    #             symbol=symbol,
    #             since=since,
    #             limit=limit,
    #             check_completeness=check_completeness,
    #             kwargs=kwargs,
    #         )
    #     if self.get_all_stop_orders_using_stop_loss_params.__name__ in defined_methods:
    #         orders += await self.get_all_stop_orders_using_stop_loss_params(
    #             symbol=symbol,
    #             since=since,
    #             limit=limit,
    #             check_completeness=check_completeness,
    #             kwargs=kwargs,
    #         )
    #     return orders

    # async def get_all_orders_default(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> list:
    #     if self.client.has.get("fetchOrders"):
    #         with self.error_describer():
    #             return await self.exchange_manager.exchange.parse_orders(
    #                 await self.client.fetch_orders(
    #                     symbol=symbol, since=since, limit=limit, params=kwargs
    #                 ),
    #                 check_completeness=check_completeness,
    #             )
    #     else:
    #         raise octobot_trading.errors.NotSupported(
    #             "This exchange doesn't support fetchOrders"
    #         )

    # async def get_all_stop_orders_using_stop_loss_params(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> list:
    #     try:
    #         if kwargs := self.exchange_manager.exchange.custom_get_all_orders_stop_params(
    #             kwargs
    #         ):
    #             orders = await self.get_all_orders_default(
    #                 symbol=symbol,
    #                 since=since,
    #                 limit=limit,
    #                 check_completeness=check_completeness,
    #                 **kwargs,
    #             )
    #             return orders
    #         return []
    #     except Exception as e:
    #         self.logger.exception(
    #             e,
    #             True,
    #             "Failed to fetch all stop orders using"
    #             " get_all_stop_order_using_stop_loss_endpoint",
    #         )
    #         return []

    # async def get_open_orders(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> list:
    #     """
    #     all known get_closed_orders methods should be added here so untested exchanges have higher chance of success
    #     """
    #     limit = self.cut_order_pagination_limit(limit)
    #     defined_methods = self.connector_config.GET_OPEN_ORDERS_METHODS
    #     orders = []
    #     if self.get_open_orders_default.__name__ in defined_methods:
    #         orders += await self.get_open_orders_default(
    #             symbol, since, limit, check_completeness=check_completeness, **kwargs
    #         )
    #     if self.get_open_stop_orders_using_stop_loss_params.__name__ in defined_methods:
    #         orders += await self.get_open_stop_orders_using_stop_loss_params(
    #             symbol, since, limit, check_completeness=check_completeness, **kwargs
    #         )
    #     return orders

    # async def get_open_orders_default(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> list:
    #     if self.client.has.get("fetchOpenOrders"):
    #         with self.error_describer():
    #             return await self.exchange_manager.exchange.parse_orders(
    #                 await self.client.fetch_open_orders(
    #                     symbol=symbol, since=since, limit=limit, params=kwargs
    #                 ),
    #                 check_completeness=check_completeness,
    #             )
    #     else:
    #         raise octobot_trading.errors.NotSupported(
    #             "This exchange doesn't support fetchOpenOrders"
    #         )

    # async def get_open_stop_orders_using_stop_loss_params(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> list:
    #     try:
    #         if kwargs := self.exchange_manager.exchange.custom_get_open_orders_stop_params(
    #             kwargs
    #         ):
    #             open_orders = await self.get_open_orders_default(
    #                 symbol=symbol,
    #                 since=since,
    #                 limit=limit,
    #                 check_completeness=check_completeness,
    #                 **kwargs,
    #             )
    #             return open_orders
    #         return []
    #     except Exception as e:
    #         self.logger.exception(
    #             e,
    #             True,
    #             "Failed to fetch open stop orders using"
    #             " get_open_stop_orders_using_stop_loss_params",
    #         )
    #         return []

    # async def get_closed_orders(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> list:
    #     """
    #     all known get_closed_orders methods should be added here so untested exchanges have higher chance of success
    #     """
    #     limit = self.cut_order_pagination_limit(limit)
    #     defined_methods = self.connector_config.GET_CLOSED_ORDERS_METHODS
    #     orders = []
    #     if self.get_closed_orders_default.__name__ in defined_methods:
    #         orders += await self.get_closed_orders_default(
    #             symbol, since, limit, check_completeness=check_completeness, **kwargs
    #         )
    #     if (
    #         self.get_closed_stop_orders_using_stop_loss_params.__name__
    #         in defined_methods
    #     ):
    #         orders += await self.get_closed_stop_orders_using_stop_loss_params(
    #             symbol, since, limit, check_completeness=check_completeness, **kwargs
    #         )
    #     return orders

    # async def get_closed_orders_default(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> list:
    #     if self.client.has.get("fetchClosedOrders"):
    #         with self.error_describer():
    #             raw_order = await self.client.fetch_closed_orders(
    #                 symbol=symbol, since=since, limit=limit, params=kwargs
    #             )
    #             return await self.exchange_manager.exchange.parse_orders(
    #                 raw_order, check_completeness=check_completeness
    #             )
    #     else:
    #         raise octobot_trading.errors.NotSupported(
    #             "This exchange doesn't support fetchClosedOrders"
    #         )

    # async def get_closed_stop_orders_using_stop_loss_params(
    #     self, symbol, since, limit, check_completeness: bool = True, **kwargs
    # ) -> list:
    #     try:
    #         if kwargs := self.exchange_manager.exchange.custom_get_closed_orders_stop_params(
    #             kwargs
    #         ):
    #             orders = await self.get_closed_orders_default(
    #                 symbol=symbol,
    #                 since=since,
    #                 limit=limit,
    #                 check_completeness=check_completeness,
    #                 **kwargs,
    #             )
    #             return orders
    #     except Exception as e:
    #         self.logger.exception(
    #             e,
    #             True,
    #             "Failed to fetch closed stop orders using"
    #             " get_closed_stop_orders_using_stop_loss_params",
    #         )
    #     return []

    # def cut_order_pagination_limit(self, limit: int) -> typing.Optional[int]:
    #     if self.connector_config.MAX_ORDER_PAGINATION_LIMIT:
    #         return min(self.connector_config.MAX_ORDER_PAGINATION_LIMIT, limit)
    #     else:
    #         return limit

    # async def get_my_recent_trades(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> list:
    #     """
    #     all known get_my_recent_trades methods should be added here
    #     """
    #     limit = self.cut_recent_trades_pagination_limit(limit)
    #     defined_methods = self.connector_config.GET_MY_RECENT_TRADES_METHODS
    #     error_messages = ""
    #     if self.get_my_recent_trades_default.__name__ in defined_methods:
    #         fetched_trades, error_message = await self.get_my_recent_trades_default(
    #             symbol=symbol,
    #             since=since,
    #             limit=limit,
    #             check_completeness=check_completeness,
    #             **kwargs,
    #         )
    #         if fetched_trades:
    #             return fetched_trades
    #         elif error_message:
    #             error_messages += error_message
    #     if self.get_my_recent_trades_using_closed_orders.__name__ in defined_methods:
    #         (
    #             fetched_trades,
    #             error_message,
    #         ) = await self.get_my_recent_trades_using_closed_orders(
    #             symbol=symbol,
    #             since=since,
    #             limit=limit,
    #             check_completeness=check_completeness,
    #             **kwargs,
    #         )
    #         if fetched_trades:
    #             return fetched_trades
    #         elif error_message:
    #             error_messages += error_message
    #     if error_messages != "":
    #         raise octobot_trading.errors.NotSupported(
    #             "This exchange doesn't support fetching trade history.\n"
    #             f"Errors: {error_messages}"
    #         )
    #     self.logger.warning(
    #         "No trades found when fetching my trades. "
    #         f"This is only normal if you haven't traded on {self.name} {symbol} yet"
    #     )
    #     return []

    # async def get_my_recent_trades_default(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> typing.Tuple[list or None, str or None]:
    #     try:
    #         if self.client.has.get("fetchMyTrades"):
    #             return (
    #                 await self.exchange_manager.exchange.parse_trades(
    #                     await self.client.fetchMyTrades(
    #                         symbol=symbol, since=since, limit=limit, params=kwargs
    #                     ),
    #                     check_completeness=check_completeness,
    #                 ),
    #                 None,
    #             )
    #         else:
    #             return (
    #                 None,
    #                 "Failed to fetch recent trades using get_my_recent_trades_default - "
    #                 "error: Exchange doesn't have a fetchMyTrades method\n",
    #             )
    #     except Exception as e:
    #         return (
    #             None,
    #             f"Failed to fetch recent trades using get_my_recent_trades_default - error: {e}",
    #         )

    # async def get_my_recent_trades_using_closed_orders(
    #     self,
    #     symbol: str = None,
    #     since: int = None,
    #     limit: int = None,
    #     check_completeness: bool = True,
    #     **kwargs: dict,
    # ) -> typing.Tuple[list or None, str or None]:
    #     try:
    #         closed_orders = await self.get_closed_orders(
    #             symbol=symbol,
    #             since=since,
    #             limit=limit,
    #             check_completeness=check_completeness,
    #             **kwargs,
    #         )
    #         trades = []
    #         for order in closed_orders:
    #             if (
    #                 order[ecoc.STATUS.value] == OrderStatus.FILLED.value
    #                 or order[ecoc.STATUS.value] == OrderStatus.CLOSED.value
    #             ):
    #                 trades.append(order)
    #         return trades, None
    #     except Exception as e:
    #         return (
    #             None,
    #             f"Failed to fetch recent trades using get_my_recent_trades_using_closed_orders: {e}",
    #         )

    # def cut_recent_trades_pagination_limit(self, limit: int) -> typing.Union[int, None]:
    #     if self.connector_config.MAX_RECENT_TRADES_PAGINATION_LIMIT:
    #         return min(self.connector_config.MAX_RECENT_TRADES_PAGINATION_LIMIT, limit)
    #     else:
    #         return limit

    # async def get_trade(
    #     self, trade_id, symbol, check_completeness=True
    # ) -> typing.Union[None, dict]:
    #     trades = await self.get_my_recent_trades(
    #         symbol, check_completeness=check_completeness
    #     )
    #     # usually the right trade is within the last ones
    #     for trade in trades[::-1]:
    #         if trade[ecoc.ID.value] == trade_id:
    #             return trade
    #     return None  # TradeNotFound

    # async def create_order(
    #     self,
    #     order_type: enums.TraderOrderType,
    #     symbol: str,
    #     quantity: decimal.Decimal,
    #     price: decimal.Decimal = None,
    #     stop_price: decimal.Decimal = None,
    #     side: enums.TradeOrderSide = None,
    #     current_price: decimal.Decimal = None,
    #     params: dict = None,
    # ) -> typing.Optional[dict]:
    #     async with self._order_operation(
    #         order_type, symbol, quantity, price, stop_price
    #     ):
    #         raw_created_order = await self._create_order_with_retry(
    #             order_type, symbol, quantity, price, side, current_price, params
    #         )
    #         return await self.exchange_manager.exchange.parse_order(
    #             raw_created_order,
    #             order_type=order_type.value,
    #             quantity=quantity,
    #             price=price,
    #             status=enums.OrderStatus.OPEN.value,
    #             symbol=symbol,
    #             side=side.value,
    #             timestamp=time.time(),
    #         )

    # async def edit_order(
    #     self,
    #     order_id: str,
    #     order_type: enums.TraderOrderType,
    #     symbol: str,
    #     quantity: decimal.Decimal,
    #     price: decimal.Decimal,
    #     stop_price: decimal.Decimal = None,
    #     side: enums.TradeOrderSide = None,
    #     current_price: decimal.Decimal = None,
    #     params: dict = None,
    # ):
    #     # Note: on most exchange, this implementation will just replace the order by cancelling the one
    #     # which id is given and create a new one
    #     async with self._order_operation(
    #         order_type, symbol, quantity, price, stop_price
    #     ):
    #         float_quantity = float(quantity)
    #         float_price = float(price)
    #         float_stop_price = None if stop_price is None else float(stop_price)
    #         float_current_price = (
    #             None if current_price is None else float(current_price)
    #         )
    #         side = None if side is None else side.value
    #         params = {} if params is None else params
    #         params.update(
    #             self.exchange_manager.exchange_backend.get_orders_parameters(None)
    #         )
    #         edited_order = await self._edit_order(
    #             order_id,
    #             order_type,
    #             symbol,
    #             quantity=float_quantity,
    #             price=float_price,
    #             stop_price=float_stop_price,
    #             side=side,
    #             current_price=float_current_price,
    #             params=params,
    #         )
    #         return await self.exchange_manager.exchange.parse_order(
    #             edited_order,
    #             order_type=order_type.value,
    #             quantity=quantity,
    #             price=price,
    #             symbol=symbol,
    #             side=side,
    #         )

    # async def _edit_order(
    #     self,
    #     order_id: str,
    #     order_type: enums.TraderOrderType,
    #     symbol: str,
    #     quantity: float,
    #     price: float,
    #     stop_price: float = None,
    #     side: str = None,
    #     current_price: float = None,
    #     params: dict = None,
    # ):
    #     ccxt_order_type = self.get_ccxt_order_type(order_type)
    #     price_to_use = price
    #     if ccxt_order_type == enums.TradeOrderType.MARKET.value:
    #         # can't set price in market orders
    #         price_to_use = None
    #     if self.is_stop_order(ccxt_order_type):
    #         params = self.exchange_manager.exchange.custom_edit_stop_orders_params(
    #             order_id, stop_price, params
    #         )
    #     # do not use keyword arguments here as default ccxt edit order is passing *args (and not **kwargs)
    #     return await self.client.edit_order(
    #         order_id, symbol, ccxt_order_type, side, quantity, price_to_use, params
    #     )

    # @staticmethod
    # def is_stop_order(order_type: enums.TradeOrderType) -> bool:
    #     return order_type in (
    #         enums.TradeOrderType.STOP_LOSS,
    #         enums.TradeOrderType.STOP_LOSS_LIMIT,
    #     )

    # @contextlib.asynccontextmanager
    # async def _order_operation(self, order_type, symbol, quantity, price, stop_price):
    #     try:
    #         yield
    #     except ccxt.InsufficientFunds as e:
    #         self.log_order_creation_error(
    #             e, order_type, symbol, quantity, price, stop_price
    #         )
    #         self.logger.warning(str(e))
    #         raise octobot_trading.errors.MissingFunds(e)
    #     except ccxt.NotSupported:
    #         raise octobot_trading.errors.NotSupported
    #     except Exception as e:
    #         self.log_order_creation_error(
    #             e, order_type, symbol, quantity, price, stop_price
    #         )
    #         self.logger.exception(
    #             e, False, f"Unexpected error during order operation: {e}"
    #         )

    # async def _create_order_with_retry(
    #     self,
    #     order_type,
    #     symbol,
    #     quantity: decimal.Decimal,
    #     price: decimal.Decimal,
    #     side: enums.TradeOrderSide,
    #     current_price: decimal.Decimal,
    #     params,
    # ) -> dict:
    #     try:
    #         return await self._create_specific_order(
    #             order_type,
    #             symbol,
    #             quantity,
    #             price=price,
    #             side=side,
    #             current_price=current_price,
    #             params=params,
    #         )
    #     except (ccxt.InvalidOrder, ccxt.BadRequest) as e:
    #         # can be raised when exchange precision/limits rules change
    #         self.logger.debug(
    #             f"Failed to create order ({e}) : order_type: {order_type}, symbol: {symbol}. "
    #             f"This might be due to an update on {self.name} market rules. Fetching updated rules."
    #         )
    #         await self.client.load_markets(reload=True)
    #         # retry order creation with updated markets (ccxt will use the updated market values)
    #         return await self._create_specific_order(
    #             order_type,
    #             symbol,
    #             quantity,
    #             price=price,
    #             side=side,
    #             current_price=current_price,
    #             params=params,
    #         )

    # async def _create_specific_order(
    #     self,
    #     order_type,
    #     symbol,
    #     quantity: decimal.Decimal,
    #     price: decimal.Decimal = None,
    #     side: enums.TradeOrderSide = None,
    #     current_price: decimal.Decimal = None,
    #     params=None,
    # ) -> dict:
    #     raw_created_order = None
    #     float_quantity = float(quantity)
    #     float_price = float(price)
    #     float_current_price = float(current_price)
    #     side = None if side is None else side.value
    #     params = {} if params is None else params
    #     params.update(
    #         self.exchange_manager.exchange_backend.get_orders_parameters(None)
    #     )
    #     if order_type == enums.TraderOrderType.BUY_MARKET:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_market_buy_order(
    #                 symbol, float_quantity, price=float_price, params=params
    #             )
    #         )
    #     elif order_type == enums.TraderOrderType.BUY_LIMIT:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_limit_buy_order(
    #                 symbol, float_quantity, price=float_price, params=params
    #             )
    #         )
    #     elif order_type == enums.TraderOrderType.SELL_MARKET:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_market_sell_order(
    #                 symbol, float_quantity, price=float_price, params=params
    #             )
    #         )
    #     elif order_type == enums.TraderOrderType.SELL_LIMIT:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_limit_sell_order(
    #                 symbol, float_quantity, price=float_price, params=params
    #             )
    #         )
    #     elif order_type == enums.TraderOrderType.STOP_LOSS:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_market_stop_loss_order(
    #                 symbol,
    #                 float_quantity,
    #                 price=float_price,
    #                 side=side,
    #                 current_price=float_current_price,
    #                 params=params,
    #             )
    #         )
    #     elif order_type == enums.TraderOrderType.STOP_LOSS_LIMIT:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_limit_stop_loss_order(
    #                 symbol, float_quantity, price=float_price, side=side, params=params
    #             )
    #         )
    #     elif order_type == enums.TraderOrderType.TAKE_PROFIT:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_market_take_profit_order(
    #                 symbol, float_quantity, price=float_price, side=side, params=params
    #             )
    #         )
    #     elif order_type == enums.TraderOrderType.TAKE_PROFIT_LIMIT:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_limit_take_profit_order(
    #                 symbol, float_quantity, price=float_price, side=side, params=params
    #             )
    #         )
    #     elif order_type == enums.TraderOrderType.TRAILING_STOP:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_market_trailing_stop_order(
    #                 symbol, float_quantity, price=float_price, side=side, params=params
    #             )
    #         )
    #     elif order_type == enums.TraderOrderType.TRAILING_STOP_LIMIT:
    #         raw_created_order = (
    #             await self.exchange_manager.exchange.create_limit_trailing_stop_order(
    #                 symbol, float_quantity, price=float_price, side=side, params=params
    #             )
    #         )
    #     return raw_created_order

    # async def create_market_buy_order(
    #     self, symbol, quantity, price=None, params=None
    # ) -> dict:
    #     return await self.client.create_market_buy_order(
    #         symbol,
    #         quantity,
    #         params=params,
    #     )

    # async def create_limit_buy_order(
    #     self, symbol, quantity, price=None, params=None
    # ) -> dict:
    #     return await self.client.create_limit_buy_order(
    #         symbol, quantity, price, params=params
    #     )

    # async def create_market_sell_order(
    #     self, symbol, quantity, price=None, params=None
    # ) -> dict:
    #     return await self.client.create_market_sell_order(
    #         symbol,
    #         quantity,
    #         params=params,
    #     )

    # async def create_limit_sell_order(
    #     self, symbol, quantity, price=None, params=None
    # ) -> dict:
    #     return await self.client.create_limit_sell_order(
    #         symbol, quantity, price, params=params
    #     )

    # async def create_market_stop_loss_order(
    #     self, symbol, quantity, price, side, current_price, params=None
    # ) -> dict:
    #     if self.client.has.get("createStopOrder"):
    #         return await self.client.create_stop_order(
    #             symbol,
    #             enums.TradeOrderType.MARKET.value,
    #             side,
    #             quantity,
    #             price,
    #             stopPrice=price,
    #             params=params,
    #         )
    #     if self.client.has.get("createStopMarketOrder"):
    #         return await self.client.create_stop_market_order(
    #             symbol, side, quantity, price, params=params
    #         )
    #     raise NotImplementedError("_create_market_stop_loss_order is not implemented")

    # async def create_limit_stop_loss_order(
    #     self, symbol, quantity, price=None, side=None, params=None
    # ) -> dict:
    #     if self.client.has.get("createStopLimitOrder"):
    #         return await self.client.create_stop_limit_order(
    #             symbol, side, quantity, price, params=params
    #         )
    #     raise NotImplementedError("_create_limit_stop_loss_order is not implemented")

    # async def create_market_take_profit_order(
    #     self, symbol, quantity, price=None, side=None, params=None
    # ) -> dict:
    #     raise NotImplementedError("_create_market_take_profit_order is not implemented")

    # async def create_limit_take_profit_order(
    #     self, symbol, quantity, price=None, side=None, params=None
    # ) -> dict:
    #     raise NotImplementedError("_create_limit_take_profit_order is not implemented")

    # async def create_market_trailing_stop_order(
    #     self, symbol, quantity, price=None, side=None, params=None
    # ) -> dict:
    #     raise NotImplementedError(
    #         "_create_market_trailing_stop_order is not implemented"
    #     )

    # async def create_limit_trailing_stop_order(
    #     self, symbol, quantity, price=None, side=None, params=None
    # ) -> dict:
    #     raise NotImplementedError(
    #         "_create_limit_trailing_stop_order is not implemented"
    #     )

    # async def cancel_order(
    #     self, order_id: str, symbol: str = None, **kwargs: dict
    # ) -> enums.OrderStatus:
    #     return await self.cancel_order_default(order_id, symbol=symbol, **kwargs)

    # async def cancel_order_default(
    #     self, order_id: str, symbol: str = None, **kwargs: dict
    # ) -> enums.OrderStatus:
    #     cancel_resp_message = None
    #     try:
    #         with self.error_describer():
    #             cancel_resp = await self.client.cancel_order(
    #                 order_id, symbol=symbol, params=kwargs
    #             )
    #         cancel_resp_message = f" - Cancel response: {cancel_resp or 'no response'}"
    #     except ccxt.OrderNotFound:
    #         raise octobot_trading.errors.OrderToEditNotFoundError(
    #             f"Trying to cancel order (id {order_id}) with cancel_order_default "
    #             f"but order was not found{cancel_resp_message or ''}\n",
    #         )
    #     except (ccxt.NotSupported, octobot_trading.errors.NotSupported) as e:
    #         raise octobot_trading.errors.OrderCancelNotSupportedError(
    #             f"cancel_order_default is not supported. Error: {e}{cancel_resp_message or ''}\n",
    #         )
    #     except Exception as e:
    #         raise octobot_trading.errors.OrderCancelUnknownError(
    #             f"Order {order_id} failed to cancel using "
    #             f"| {e} ({e.__class__.__name__}){cancel_resp_message or ''}\n",
    #         )
    #     if await self.check_if_canceled(order_id, symbol, cancel_resp):
    #         return enums.OrderStatus.CANCELED
    #     return enums.OrderStatus.PENDING_CANCEL

    # async def check_if_canceled(self, order_id, symbol, cancel_resp=None) -> bool:
    #     try:
    #         # check if canceled
    #         if type(cancel_resp) is dict:
    #             try:
    #                 if personal_data.parse_is_cancelled(cancel_resp):
    #                     return True
    #             except Exception:
    #                 pass
    #         if cancelled_order := await self.get_order(order_id, symbol=symbol):
    #             if personal_data.parse_is_cancelled(cancelled_order):
    #                 return True
    #             else:
    #                 return False
    #         else:
    #             # Order is not found: it has successfully been cancelled
    #             # (some exchanges don't allow to get a cancelled order).
    #             return True
    #     except ccxt.OrderNotFound:
    #         # Order is not found: it has successfully been cancelled
    #         # (some exchanges don't allow to get a cancelled order).
    #         return True

    # @staticmethod
    # def get_ccxt_order_type(order_type: enums.TraderOrderType):
    #     if order_type in (
    #         enums.TraderOrderType.BUY_LIMIT,
    #         enums.TraderOrderType.SELL_LIMIT,
    #         enums.TraderOrderType.STOP_LOSS_LIMIT,
    #         enums.TraderOrderType.TAKE_PROFIT_LIMIT,
    #         enums.TraderOrderType.TRAILING_STOP_LIMIT,
    #     ):
    #         return enums.TradeOrderType.LIMIT.value
    #     if order_type in (
    #         enums.TraderOrderType.BUY_MARKET,
    #         enums.TraderOrderType.SELL_MARKET,
    #         enums.TraderOrderType.STOP_LOSS,
    #         enums.TraderOrderType.TAKE_PROFIT,
    #         enums.TraderOrderType.TRAILING_STOP,
    #     ):
    #         return enums.TradeOrderType.MARKET.value
    #     raise RuntimeError(f"Unknown order type: {order_type}")

    # def get_trade_fee(self, symbol, order_type, quantity, price, taker_or_maker):
    #     fees = self.client.calculate_fee(
    #         symbol=symbol,
    #         type=order_type,
    #         side=exchanges.get_order_side(order_type),
    #         amount=float(quantity),
    #         price=float(price),
    #         takerOrMaker=taker_or_maker,
    #     )
    #     fees[enums.FeePropertyColumns.COST.value] = decimal.Decimal(
    #         str(fees[enums.FeePropertyColumns.COST.value])
    #     )
    #     if self.exchange_manager.is_future:
    #         # fees on futures are wrong
    #         rate = fees[enums.FeePropertyColumns.RATE.value]
    #         # avoid using ccxt computed fees as they are often wrong
    #         # see https://docs.ccxt.com/en/latest/manual.html#trading-fees
    #         parsed_symbol = commons_symbols.parse_symbol(symbol)
    #         if self.exchange_manager.exchange.get_pair_future_contract(
    #             symbol
    #         ).is_inverse_contract():
    #             fees[enums.FeePropertyColumns.COST.value] = (
    #                 decimal.Decimal(str(rate)) * quantity
    #             )
    #             fees[enums.FeePropertyColumns.CURRENCY.value] = parsed_symbol.base
    #         else:
    #             fees[enums.FeePropertyColumns.COST.value] = (
    #                 decimal.Decimal(str(rate)) * quantity * price
    #             )
    #             fees[enums.FeePropertyColumns.CURRENCY.value] = parsed_symbol.quote
    #     return fees

    # def get_fees(self, symbol):
    #     try:
    #         market_status = self.client.market(symbol)
    #         return {
    #             enums.ExchangeConstantsMarketPropertyColumns.TAKER.value: market_status.get(
    #                 enums.ExchangeConstantsMarketPropertyColumns.TAKER.value
    #             )
    #             or self.config[octobot_commons.constants.CONFIG_SIMULATOR][
    #                 octobot_commons.constants.CONFIG_SIMULATOR_FEES
    #             ][octobot_commons.constants.CONFIG_SIMULATOR_FEES_TAKER],
    #             enums.ExchangeConstantsMarketPropertyColumns.MAKER.value: market_status.get(
    #                 enums.ExchangeConstantsMarketPropertyColumns.MAKER.value
    #             )
    #             or self.config[octobot_commons.constants.CONFIG_SIMULATOR][
    #                 octobot_commons.constants.CONFIG_SIMULATOR_FEES
    #             ][octobot_commons.constants.CONFIG_SIMULATOR_FEES_MAKER],
    #             enums.ExchangeConstantsMarketPropertyColumns.FEE.value: market_status.get(
    #                 enums.ExchangeConstantsMarketPropertyColumns.FEE.value
    #             )
    #             or constants.CONFIG_DEFAULT_FEES,
    #         }

    #     except ccxt.NotSupported:
    #         raise octobot_trading.errors.NotSupported
    #     except Exception as e:
    #         self.logger.exception(e, True, f"Fees data for {symbol} was not found")
    #         return {
    #             enums.ExchangeConstantsMarketPropertyColumns.TAKER.value: constants.CONFIG_DEFAULT_FEES,
    #             enums.ExchangeConstantsMarketPropertyColumns.MAKER.value: constants.CONFIG_DEFAULT_FEES,
    #             enums.ExchangeConstantsMarketPropertyColumns.FEE.value: constants.CONFIG_DEFAULT_FEES,
    #         }

    # def get_uniform_timestamp(self, timestamp):
    #     return timestamp / octobot_commons.constants.MSECONDS_TO_SECONDS

    # def get_exchange_current_time(self):
    #     return self.get_uniform_timestamp(self.client.milliseconds())

    # async def stop(self) -> None:
    #     self.logger.info(f"Closing connection.")
    #     await self.client.close()
    #     self.logger.info(f"Connection closed.")
    #     self.exchange_manager = None

    # def get_pair_from_exchange(self, pair) -> typing.Optional[str]:
    #     try:
    #         return self.client.market(pair)["symbol"]
    #     except ccxt.BadSymbol:
    #         try:
    #             return self.client.markets_by_id[pair]["symbol"]
    #         except KeyError:
    #             self.logger.error(f"Failed to get market of {pair}")
    #     return None

    # def get_split_pair_from_exchange(self, pair) -> (str, str):
    #     try:
    #         market_data: dict = self.client.market(pair)
    #         return market_data["base"], market_data["quote"]
    #     except ccxt.BadSymbol:
    #         try:
    #             return (
    #                 self.client.markets_by_id[pair]["base"],
    #                 self.client.markets_by_id[pair]["quote"],
    #             )
    #         except KeyError:
    #             self.logger.error(f"Failed to get market of {pair}")
    #             return None, None

    # def get_exchange_pair(self, pair) -> str:
    #     if pair in self.client.symbols:
    #         try:
    #             return self.client.market(pair)["id"]
    #         except KeyError:
    #             pass
    #     raise ValueError(f"{pair} is not supported")

    # def get_pair_cryptocurrency(self, pair) -> str:
    #     if pair in self.client.symbols:
    #         try:
    #             return self.client.market(pair)["base"]
    #         except KeyError:
    #             pass
    #     raise ValueError(f"{pair} is not supported")

    # def get_default_balance(self):
    #     return self.client.account()

    # def get_rate_limit(self):
    #     return self.exchange_type.rateLimit / 1000

    # def set_sandbox_mode(self, is_sandboxed):
    #     try:
    #         self.client.setSandboxMode(is_sandboxed)
    #     except ccxt.NotSupported as error:
    #         default_type = self.client.options.get("defaultType", None)
    #         additional_info = f" in type {default_type}" if default_type else ""
    #         self.logger.warning(
    #             f"{self.name} does not support sandboxing {additional_info}: {error}"
    #         )
    #         # raise exception to stop this exchange and prevent dealing with a real funds exchange
    #         raise error

    # """
    # Parsers
    # """

    # def parse_balance(self, balance):
    #     return personal_data.parse_decimal_portfolio(self.client.parse_balance(balance))

    # def parse_ohlcv(self, ohlcv):
    #     return self.uniformize_candles_if_necessary(self.client.parse_ohlcv(ohlcv))

    # def parse_order_book(self, order_book):
    #     return self.client.parse_order_book(order_book)

    # def parse_order_book_ticker(self, order_book_ticker):
    #     return order_book_ticker

    # def parse_timestamp(self, data_dict, timestamp_key, default_value=None, ms=False):
    #     parsed_timestamp = self.client.parse8601(
    #         self.client.safe_string(data_dict, timestamp_key)
    #     )
    #     return (
    #         (parsed_timestamp if ms else parsed_timestamp * 10**-3)
    #         if parsed_timestamp
    #         else default_value
    #     )

    # def parse_currency(self, currency):
    #     return self.client.safe_currency_code(currency)

    # def parse_account(self, account):
    #     return enums.AccountTypes[account.lower()]

    # def get_max_handled_pair_with_time_frame(self) -> int:
    #     """
    #     Override when necessary
    #     :return: the maximum number of simultaneous pairs * time_frame that this exchange can handle.
    #     """
    #     # 15 pairs, each on 3 time frames
    #     return 45

    # @contextlib.contextmanager
    # def error_describer(self):
    #     try:
    #         yield
    #     except ccxt.DDoSProtection as e:
    #         # raised upon rate limit issues, last response data might have details on what is happening
    #         if self.exchange_manager.exchange.should_log_on_ddos_exception(e):
    #             self.logger.error(
    #                 f"DDoSProtection triggered [{e} ({e.__class__.__name__})]. "
    #                 f"Last response headers: {self.client.last_response_headers} "
    #                 f"Last json response: {self.client.last_json_response}"
    #             )
    #         raise
