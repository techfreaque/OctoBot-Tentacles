#  Drakkar-Software OctoBot-Trading
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
import json
from octobot_trading.api.exchange import get_exchange_ids

import octobot_trading.enums as trading_enums
import octobot_trading.personal_data.portfolios.portfolio_util as portfolio_util
import octobot_trading.api as trading_api
import octobot_backtesting.api as backtesting_api
import octobot_commons.symbols.symbol_util as symbol_util
import octobot_commons.constants
import octobot_commons.enums as commons_enums
import octobot_commons.time_frame_manager as time_frame_manager
import octobot_commons.logging


class RunAnalysisData:
    price_data = None
    trades_data = None
    ref_market = None
    starting_portfolio = None
    moving_portfolio_data = None
    trading_type = None
    metadata = None
    trading_transactions_history = None
    total_start_balance_in_ref_market = None
    pairs = None
    longest_candles = None
    funding_fees_history_by_pair = None
    portfolio_value_times = None
    portfolio_values = None
    exchange = None
    realized_pnl_x_data: list = None
    realized_pnl_trade_gains_data: list = None
    realized_pnl_cumulative: list = None
    wins_and_losses_x_data: list = []
    wins_and_losses_data: list = []
    win_rates_x_data: list = []
    win_rates_data: list = []
    best_case_growth_x_data: list = []
    best_case_growth_data: list = []

    def __init__(self, ctx, run_database, run_display, analysis_settings):
        self.run_database = run_database
        self.run_display = run_display
        self.ctx = ctx
        self.analysis_settings = analysis_settings

    async def load_base_data(self):
        await self.load_historical_values()
        self.trading_transactions_history = await self.load_or_generate_transactions(
            transaction_types=(
                trading_enums.TransactionType.TRADING_FEE.value,
                trading_enums.TransactionType.FUNDING_FEE.value,
                trading_enums.TransactionType.REALIZED_PNL.value,
                trading_enums.TransactionType.CLOSE_REALIZED_PNL.value,
            )
        )

        self.total_start_balance_in_ref_market = self.starting_portfolio[
            self.ref_market
        ][
            "total"
        ]  # todo all coins balance
        self.pairs = list(self.trades_data)
        self.set_longest_candles()
        await self.generate_historical_portfolio_value()

    def get_live_candles(self, symbol, time_frame):
        # todo get/download history from first tradetime or start time
        # todo multi exchange
        exchange_manager = trading_api.get_exchange_manager_from_exchange_id(
            get_exchange_ids()[0]
        )
        _raw_candles = trading_api.get_symbol_historical_candles(
            trading_api.get_symbol_data(exchange_manager, symbol, allow_creation=False),
            time_frame,
        )
        raw_candles = []
        for index in range(len(_raw_candles[0])):
            raw_candles.append(
                [
                    # convert candles timestamp in millis
                    _raw_candles[commons_enums.PriceIndexes.IND_PRICE_TIME.value][index]
                    * 1000,
                    _raw_candles[commons_enums.PriceIndexes.IND_PRICE_OPEN.value][
                        index
                    ],
                    _raw_candles[commons_enums.PriceIndexes.IND_PRICE_HIGH.value][
                        index
                    ],
                    _raw_candles[commons_enums.PriceIndexes.IND_PRICE_LOW.value][index],
                    _raw_candles[commons_enums.PriceIndexes.IND_PRICE_CLOSE.value][
                        index
                    ],
                    _raw_candles[commons_enums.PriceIndexes.IND_PRICE_VOL.value][index],
                ]
            )
        return raw_candles

    async def get_backtesting_candles(self, candles_sources, symbol, time_frame):
        raw_candles = await backtesting_api.get_all_ohlcvs(
            candles_sources[0][commons_enums.DBRows.VALUE.value],
            self.exchange,
            symbol,
            commons_enums.TimeFrames(time_frame),
            inferior_timestamp=self.metadata[commons_enums.DBRows.START_TIME.value],
            superior_timestamp=self.metadata[commons_enums.DBRows.END_TIME.value],
        )
        # convert candles timestamp in millis
        for candle in raw_candles:
            candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] = (
                candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value] * 1000
            )
        return raw_candles

    async def get_trades(self, symbol):
        return await self.run_database.get_trades_db().select(
            commons_enums.DBTables.TRADES.value,
            (await self.run_database.get_orders_db().search()).symbol == symbol,
        )

    async def load_metadata(self):
        self.metadata = (
            await self.run_database.get_run_db().all(
                commons_enums.DBTables.METADATA.value
            )
        )[0]

    async def load_transactions(self, transaction_type=None, transaction_types=None):
        if transaction_type is not None:
            query = (
                await self.run_database.get_transactions_db().search()
            ).type == transaction_type
        elif transaction_types is not None:
            query = (
                await self.run_database.get_transactions_db().search()
            ).type.one_of(transaction_types)
        else:
            return await self.run_database.get_transactions_db().all(
                commons_enums.DBTables.TRANSACTIONS.value
            )
        return await self.run_database.get_transactions_db().select(
            commons_enums.DBTables.TRANSACTIONS.value, query
        )

    def load_starting_portfolio(self) -> dict:
        portfolio = self.metadata[
            commons_enums.BacktestingMetadata.START_PORTFOLIO.value
        ]
        self.starting_portfolio = json.loads(portfolio.replace("'", '"'))

    async def load_historical_values(
        self,
        exchange=None,
        with_candles=True,
        with_trades=True,
        with_portfolio=True,
        time_frame=None,
    ):
        self.price_data = {}
        self.trades_data = {}
        self.moving_portfolio_data = {}
        self.trading_type = "spot"
        await self.load_metadata()
        self.load_starting_portfolio()
        self.exchange = (
            exchange
            or self.metadata[commons_enums.DBRows.EXCHANGES.value][0]
            or (
                self.run_database.run_dbs_identifier.context.exchange_name
                if self.run_database.run_dbs_identifier.context
                else None
            )
        )  # TODO handle multi exchanges
        self.ref_market = self.metadata[commons_enums.DBRows.REFERENCE_MARKET.value]
        self.trading_type = self.metadata[commons_enums.DBRows.TRADING_TYPE.value]
        contracts = (
            self.metadata[commons_enums.DBRows.FUTURE_CONTRACTS.value][self.exchange]
            if self.trading_type == "future"
            else {}
        )
        # init data
        for pair in self.metadata[commons_enums.DBRows.SYMBOLS.value]:
            symbol = symbol_util.parse_symbol(pair).base
            is_inverse_contract = (
                self.trading_type == "future"
                and trading_api.is_inverse_future_contract(
                    trading_enums.FutureContractType(contracts[pair]["contract_type"])
                )
            )
            if symbol != self.ref_market or is_inverse_contract:
                candles_sources = await self.run_database.get_symbol_db(
                    self.exchange, pair
                ).all(commons_enums.DBTables.CANDLES_SOURCE.value)
                if time_frame is None:
                    time_frames = [
                        source[commons_enums.DBRows.TIME_FRAME.value]
                        for source in candles_sources
                    ]
                    time_frame = (
                        time_frame_manager.find_min_time_frame(time_frames)
                        if time_frames
                        else time_frame
                    )
                if with_candles and pair not in self.price_data:
                    try:
                        self.price_data[pair] = await self.get_candles(
                            candles_sources, pair, time_frame
                        )
                    except KeyError as error:
                        raise CandlesLoadingError(
                            f"Unable to load {pair}/{time_frames} candles"
                        ) from error
                if with_trades and pair not in self.trades_data:
                    self.trades_data[pair] = await self.get_trades(pair)
            if with_portfolio:
                try:
                    self.moving_portfolio_data[symbol] = self.starting_portfolio[
                        symbol
                    ][octobot_commons.constants.PORTFOLIO_TOTAL]
                except KeyError:
                    self.moving_portfolio_data[symbol] = 0
                try:
                    self.moving_portfolio_data[
                        self.ref_market
                    ] = self.starting_portfolio[self.ref_market][
                        octobot_commons.constants.PORTFOLIO_TOTAL
                    ]
                except KeyError:
                    self.moving_portfolio_data[self.ref_market] = 0

    async def get_candles(self, candles_sources, pair, time_frame) -> list:
        if (
            candles_sources[0][commons_enums.DBRows.VALUE.value]
            == octobot_commons.constants.LOCAL_BOT_DATA
        ):

            return self.get_live_candles(pair, time_frame)
        else:
            return await self.get_backtesting_candles(candles_sources, pair, time_frame)

    async def load_grouped_funding_fees(self):
        if not self.funding_fees_history_by_pair:
            funding_fees_history = await self.load_transactions(
                transaction_type=trading_enums.TransactionType.FUNDING_FEE.value,
            )
            funding_fees_history = sorted(
                funding_fees_history,
                key=lambda f: f[commons_enums.PlotAttributes.X.value],
            )
            self.funding_fees_history_by_pair = {}
            for funding_fee in funding_fees_history:
                try:
                    self.funding_fees_history_by_pair[
                        funding_fee[commons_enums.PlotAttributes.SYMBOL.value]
                    ].append(funding_fee)
                except KeyError:
                    self.funding_fees_history_by_pair[
                        funding_fee[commons_enums.PlotAttributes.SYMBOL.value]
                    ] = [funding_fee]

    async def generate_historical_portfolio_value(self):
        if self.trading_type == "future":
            # TODO: historical unrealized pnl
            pass
        for pair in self.trades_data:
            self.trades_data[pair] = sorted(
                self.trades_data[pair],
                key=lambda tr: tr[commons_enums.PlotAttributes.X.value],
            )
        self.portfolio_value_times = []
        self.portfolio_values = []
        if self.pairs:
            await self.load_grouped_funding_fees()
            self.portfolio_value_times = [
                candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value]
                for candle in self.longest_candles
            ]
            self.portfolio_values = [0] * len(self.longest_candles)
            trade_index_by_pair = {p: 0 for p in self.pairs}
            funding_fees_index_by_pair = {p: 0 for p in self.pairs}
            # TODO multi exchanges
            exchange_name = self.metadata[commons_enums.DBRows.EXCHANGES.value][0]
            # TODO hedge mode with multi position by pair
            # if metadata[commons_enums.DBRows.FUTURE_CONTRACTS.value] and \
            #         exchange_name in metadata[commons_enums.DBRows.FUTURE_CONTRACTS.value]:
            #     positions_by_pair = {
            #         pair: _position_factory(pair,
            #                                 metadata[commons_enums.DBRows.FUTURE_CONTRACTS.value][exchange_name][pair])
            #         for pair in pairs
            #     }
            # else:
            #     positions_by_pair = {}
            # TODO update position instead of portfolio when filled orders and apply position unrealized pnl to portfolio
            trades_without_fees = False
            for index, ref_candle in enumerate(self.longest_candles):
                handled_currencies = []
                for pair in self.pairs:
                    try:
                        other_candle = self.price_data[pair][index]
                    except IndexError:
                        continue  # no price for this candle and pair
                    symbol, ref_market = symbol_util.parse_symbol(pair).base_and_quote()
                    # part 1: compute portfolio total value after trade update when any
                    # 1.1: trades
                    # start iteration where it last stopped to reduce complexity
                    for trade_index, trade in enumerate(
                        self.trades_data[pair][trade_index_by_pair[pair] :]
                    ):
                        # todo remove when trades with 0 volume arent stored anymore
                        if not trade[commons_enums.PlotAttributes.VOLUME.value]:
                            continue

                        # handle trades that are both older and at the
                        # current candle starting from the last trade index
                        # (older trades to handle the ones that might be
                        # from candles we dont have data one)
                        if (
                            trade[commons_enums.PlotAttributes.X.value]
                            <= ref_candle[
                                commons_enums.PriceIndexes.IND_PRICE_TIME.value
                            ]
                        ):
                            if (
                                trade[commons_enums.PlotAttributes.SIDE.value]
                                == trading_enums.TradeOrderSide.SELL.value
                            ):
                                self.moving_portfolio_data[symbol] -= trade[
                                    commons_enums.PlotAttributes.VOLUME.value
                                ]
                                self.moving_portfolio_data[ref_market] += (
                                    trade[commons_enums.PlotAttributes.VOLUME.value]
                                    * trade[commons_enums.PlotAttributes.Y.value]
                                )
                            else:
                                self.moving_portfolio_data[symbol] += trade[
                                    commons_enums.PlotAttributes.VOLUME.value
                                ]
                                self.moving_portfolio_data[ref_market] -= (
                                    trade[commons_enums.PlotAttributes.VOLUME.value]
                                    * trade[commons_enums.PlotAttributes.Y.value]
                                )
                            if trade[commons_enums.DBTables.FEES_AMOUNT.value]:
                                self.moving_portfolio_data[
                                    trade[commons_enums.DBTables.FEES_CURRENCY.value]
                                ] -= trade[commons_enums.DBTables.FEES_AMOUNT.value]
                            else:
                                trades_without_fees = True

                            # last trade case: as there is not trade afterwards,
                            # the next condition would never be filled,
                            # force trade_index_by_pair[pair] increment
                            if all(
                                it_trade[commons_enums.PlotAttributes.X.value]
                                == trade[commons_enums.PlotAttributes.X.value]
                                for it_trade in self.trades_data[pair][
                                    trade_index_by_pair[pair] :
                                ]
                            ):
                                trade_index_by_pair[pair] += 1
                                break

                        if (
                            trade[commons_enums.PlotAttributes.X.value]
                            > ref_candle[
                                commons_enums.PriceIndexes.IND_PRICE_TIME.value
                            ]
                        ):
                            # no need to continue iterating,
                            # save current index for new candle
                            trade_index_by_pair[pair] += trade_index
                            break
                    # 1.2: funding fees
                    # start iteration where it last stopped to reduce complexity
                    for funding_fee_index, funding_fee in enumerate(
                        self.funding_fees_history_by_pair.get(pair, [])[
                            funding_fees_index_by_pair[pair] :
                        ]
                    ):
                        if (
                            funding_fee[commons_enums.PlotAttributes.X.value]
                            == ref_candle[
                                commons_enums.PriceIndexes.IND_PRICE_TIME.value
                            ]
                        ):
                            self.moving_portfolio_data[
                                funding_fee[
                                    trading_enums.FeePropertyColumns.CURRENCY.value
                                ]
                            ] -= funding_fee["quantity"]
                        if (
                            funding_fee[commons_enums.PlotAttributes.X.value]
                            > ref_candle[
                                commons_enums.PriceIndexes.IND_PRICE_TIME.value
                            ]
                        ):
                            # no need to continue iterating,
                            # save current index for new candle
                            funding_fees_index_by_pair[pair] = funding_fee_index  # TODO
                            break
                    # part 2: now that portfolio is up to date,
                    # compute portfolio total value
                    if (
                        other_candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value]
                        == ref_candle[commons_enums.PriceIndexes.IND_PRICE_TIME.value]
                    ):
                        if symbol not in handled_currencies:
                            self.portfolio_values[index] = (
                                self.portfolio_values[index]
                                + self.moving_portfolio_data[symbol]
                                * other_candle[
                                    commons_enums.PriceIndexes.IND_PRICE_OPEN.value
                                ]
                            )
                            handled_currencies.append(symbol)
                        if ref_market not in handled_currencies:
                            self.portfolio_values[index] = (
                                self.portfolio_values[index]
                                + self.moving_portfolio_data[ref_market]
                            )
                            handled_currencies.append(ref_market)
            if trades_without_fees:
                get_logger().error(
    "Trade found without fees, "
    "pnl calculation will not be accurate."
    )

    def set_longest_candles(self) -> list:
        longest_pair = None
        longest_len = 0
        for pair, candles in self.price_data.items():
            if pair not in self.pairs:
                continue
            if (new_len := len(candles)) > longest_len:
                longest_len = new_len
                longest_pair = pair
        self.longest_candles = self.price_data[longest_pair]

    def _read_pnl_from_transactions(
        self,
        x_data,
        pnl_data,
        cumulative_pnl_data,
        x_as_trade_count,
    ):
        previous_value = 0
        for transaction in self.trading_transactions_history:
            transaction_pnl = (
                0
                if transaction["realized_pnl"] is None
                else transaction["realized_pnl"]
            )
            transaction_quantity = (
                0 if transaction["quantity"] is None else transaction["quantity"]
            )
            local_quantity = transaction_pnl + transaction_quantity
            cumulated_pnl = local_quantity + previous_value
            pnl_data.append(local_quantity)
            cumulative_pnl_data.append(cumulated_pnl)
            previous_value = cumulated_pnl
            if x_as_trade_count:
                x_data.append(len(pnl_data) - 1)
            else:
                x_data.append(transaction[commons_enums.PlotAttributes.X.value])

    async def load_realized_pnl(
        self,
        x_as_trade_count=True,
    ):
        # PNL:
        # 1. open position: consider position opening fee from PNL
        # 2. close position: consider closed amount + closing fee into PNL
        # what is a trade ?
        #   futures: when position going to 0 (from long/short) => trade is closed
        #   spot: when position lowered => trade is closed
        if not (self.price_data and next(iter(self.price_data.values()))):
            return
        self.realized_pnl_x_data = [
            0
            if x_as_trade_count
            else next(iter(self.price_data.values()))[0][
                commons_enums.PriceIndexes.IND_PRICE_TIME.value
            ]
        ]
        self.realized_pnl_trade_gains_data = [0]
        self.realized_pnl_cumulative = [0]
        if self.trading_transactions_history:
            # can rely on pnl history
            self._read_pnl_from_transactions(
                self.realized_pnl_x_data,
                self.realized_pnl_trade_gains_data,
                self.realized_pnl_cumulative,
                x_as_trade_count,
            )
            # else:
            #     # recreate pnl history from trades
            #     self._read_pnl_from_trades(
            #         x_data,
            #         pnl_data,
            #         cumulative_pnl_data,
            #         x_as_trade_count,
            #     )

            if not x_as_trade_count:
                # x axis is time: add a value at the end of the axis if missing
                # to avoid a missing values at the end feeling
                last_time_value = next(iter(self.price_data.values()))[-1][
                    commons_enums.PriceIndexes.IND_PRICE_TIME.value
                ]
                if self.realized_pnl_x_data[-1] != last_time_value:
                    # append the latest value at the end of the x axis
                    self.realized_pnl_x_data.append(last_time_value)
                    self.realized_pnl_trade_gains_data.append(0)
                    self.realized_pnl_cumulative.append(
                        self.realized_pnl_cumulative[-1]
                    )

    # async def total_paid_fees(meta_database, all_trades):
    #     paid_fees = 0
    #     fees_currency = None
    #     if trading_transactions_history:
    #         for transaction in trading_transactions_history:
    #             if fees_currency is None:
    #                 fees_currency = transaction["currency"]
    #             if transaction["currency"] != fees_currency:
    #                 get_logger().error(f"Unknown funding fee value: {transaction}")
    #             else:
    #                 # - because funding fees are stored as negative number when paid (positive when "gained")
    #                 paid_fees -= transaction["quantity"]
    #     for trade in all_trades:
    #         currency = symbol_util.parse_symbol(
    #             trade[commons_enums.DBTables.SYMBOL.value]
    #         ).base
    #         if trade[commons_enums.DBTables.FEES_CURRENCY.value] == currency:
    #             if trade[commons_enums.DBTables.FEES_CURRENCY.value] == fees_currency:
    #                 paid_fees += trade[commons_enums.DBTables.FEES_AMOUNT.value]
    #             else:
    #                 paid_fees += (
    #                     trade[commons_enums.DBTables.FEES_AMOUNT.value]
    #                     * trade[commons_enums.PlotAttributes.Y.value]
    #                 )
    #         else:
    #             if trade[commons_enums.DBTables.FEES_CURRENCY.value] == fees_currency:
    #                 paid_fees += (
    #                     trade[commons_enums.DBTables.FEES_AMOUNT.value]
    #                     / trade[commons_enums.PlotAttributes.Y.value]
    #                 )
    #             else:
    #                 paid_fees += trade[commons_enums.DBTables.FEES_AMOUNT.value]
    #     return paid_fees

    def generate_wins_and_losses(self, x_as_trade_count):
        if not (self.wins_and_losses_x_data and self.wins_and_losses_data):
            if not (self.price_data and next(iter(self.price_data.values()))):
                return
            if self.trading_transactions_history:
                # can rely on pnl history
                for transaction in self.trading_transactions_history:
                    transaction_pnl = (
                        0
                        if transaction["realized_pnl"] is None
                        else transaction["realized_pnl"]
                    )
                    current_cumulative_wins = (
                        self.wins_and_losses_data[-1]
                        if self.wins_and_losses_data
                        else 0
                    )
                    if transaction_pnl < 0:
                        self.wins_and_losses_data.append(current_cumulative_wins - 1)
                    elif transaction_pnl > 0:
                        self.wins_and_losses_data.append(current_cumulative_wins + 1)
                    else:
                        continue

                    if x_as_trade_count:
                        self.wins_and_losses_x_data.append(
                            len(self.wins_and_losses_data) - 1
                        )
                    else:
                        self.wins_and_losses_x_data.append(
                            transaction[commons_enums.PlotAttributes.X.value]
                        )

    def generate_win_rates(self, x_as_trade_count):
        if not (self.win_rates_x_data and self.win_rates_data):
            if not (self.price_data and next(iter(self.price_data.values()))):
                return
            if self.trading_transactions_history:
                wins_count = 0
                losses_count = 0

                for transaction in self.trading_transactions_history:
                    transaction_pnl = (
                        0
                        if transaction["realized_pnl"] is None
                        else transaction["realized_pnl"]
                    )
                    if transaction_pnl < 0:
                        losses_count += 1
                    elif transaction_pnl > 0:
                        wins_count += 1
                    else:
                        continue

                    self.win_rates_data.append(
                        (wins_count / (losses_count + wins_count)) * 100
                    )
                    if x_as_trade_count:
                        self.win_rates_x_data.append(len(self.win_rates_data) - 1)
                    else:
                        self.win_rates_x_data.append(
                            transaction[commons_enums.PlotAttributes.X.value]
                        )

    async def get_best_case_growth_from_transactions(
        self,
        x_as_trade_count,
    ):
        if not (self.best_case_growth_x_data and self.best_case_growth_data):
            if not (self.price_data and next(iter(self.price_data.values()))):
                return
            if self.trading_transactions_history:
                (
                    self.best_case_growth_data,
                    _,
                    _,
                    _,
                    self.best_case_growth_x_data,
                ) = await portfolio_util.get_coefficient_of_determination_data(
                    transactions=self.trading_transactions_history,
                    longest_candles=self.longest_candles,
                    start_balance=self.total_start_balance_in_ref_market,
                    use_high_instead_of_end_balance=True,
                    x_as_trade_count=x_as_trade_count,
                )

    async def load_or_generate_transactions(
        self, transaction_type=None, transaction_types=None
    ):
        trading_transactions_history = await self.load_transactions(
            transaction_type=transaction_type,
            transaction_types=transaction_types,
        )
        if not trading_transactions_history:
            trading_transactions_history = self.generate_spot_transactions(
                transaction_type=transaction_type,
                transaction_types=transaction_types,
            )
        return trading_transactions_history

    def generate_spot_transactions(self, transaction_type=None, transaction_types=None):
        # todo filter by transaction type
        trading_transactions_history = []
        prev_transaction_id = 0
        buy_order_volume_by_price_by_currency = {
            symbol_util.parse_symbol(symbol).base: {} for symbol in self.trades_data
        }
        buy_fees = 0
        sell_fees = 0
        for pair, trades in self.trades_data.items():
            parsed_symbol = symbol_util.parse_symbol(pair)
            for trade in trades:
                trade_volume = trade[commons_enums.PlotAttributes.VOLUME.value]
                if not trade_volume:
                    # todo remove when trades with 0 volume arent stored anymore
                    continue
                buy_order_volume_by_price = buy_order_volume_by_price_by_currency[
                    parsed_symbol.base
                ]
                if (
                    trade[commons_enums.PlotAttributes.SIDE.value]
                    == trading_enums.TradeOrderSide.BUY.value
                ):
                    fees = trade[commons_enums.DBTables.FEES_AMOUNT.value]
                    try:
                        fees_multiplier = (
                            1
                            if trade[commons_enums.DBTables.FEES_CURRENCY.value]
                            == parsed_symbol.base
                            else 1 / trade[commons_enums.PlotAttributes.Y.value]
                        )
                    except ZeroDivisionError:
                        test = 1
                    paid_fees = fees * fees_multiplier
                    buy_fees += paid_fees * trade[commons_enums.PlotAttributes.Y.value]
                    buy_cost = (
                        trade_volume * trade[commons_enums.PlotAttributes.Y.value]
                    )
                    if (
                        trade[commons_enums.PlotAttributes.Y.value]
                        in buy_order_volume_by_price
                    ):
                        buy_order_volume_by_price[
                            buy_cost / (trade_volume - paid_fees)
                        ] += (trade_volume - paid_fees)
                    else:
                        buy_order_volume_by_price[
                            buy_cost / (trade_volume - paid_fees)
                        ] = (trade_volume - paid_fees)
                    # buy fees transaction
                    add_transaction(
                        trading_transactions_history=trading_transactions_history,
                        prev_transaction_id=prev_transaction_id,
                        trade=trade,
                        _type=trading_enums.TransactionType.TRADING_FEE.value,
                        pair=pair,
                        transaction_currency=parsed_symbol.quote,
                        transaction_quantity=-paid_fees,
                    )
                elif (
                    trade[commons_enums.PlotAttributes.SIDE.value]
                    == trading_enums.TradeOrderSide.SELL.value
                ):
                    remaining_sell_volume = trade_volume
                    volume_by_bought_prices = {}
                    for order_price in list(buy_order_volume_by_price.keys()):
                        if (
                            buy_order_volume_by_price[order_price]
                            > remaining_sell_volume
                        ):
                            buy_order_volume_by_price[
                                order_price
                            ] -= remaining_sell_volume
                            volume_by_bought_prices[order_price] = remaining_sell_volume
                            remaining_sell_volume = 0
                        elif (
                            buy_order_volume_by_price[order_price]
                            == remaining_sell_volume
                        ):
                            buy_order_volume_by_price.pop(order_price)
                            volume_by_bought_prices[order_price] = remaining_sell_volume
                            remaining_sell_volume = 0
                        else:
                            # buy_order_volume_by_price[order_price] < remaining_sell_volume
                            buy_volume = buy_order_volume_by_price.pop(order_price)
                            volume_by_bought_prices[order_price] = buy_volume
                            remaining_sell_volume -= buy_volume
                        if remaining_sell_volume <= 0:
                            break
                    if volume_by_bought_prices:
                        # use total_bought_volume only to avoid taking pre-existing open positions into account
                        # (ex if started with already 10 btc)
                        # total obtained (in ref market) – sell order fees – buy costs (in ref market before fees)
                        buy_cost = sum(
                            price * volume
                            for price, volume in volume_by_bought_prices.items()
                        )
                        fees = trade[commons_enums.DBTables.FEES_AMOUNT.value]
                        fees_multiplier = (
                            1
                            if trade[commons_enums.DBTables.FEES_CURRENCY.value]
                            == parsed_symbol.quote
                            else trade[commons_enums.PlotAttributes.Y.value]
                        )
                        sell_fees += fees * fees_multiplier
                    local_pnl = (
                        trade[commons_enums.PlotAttributes.Y.value] * trade_volume
                        - (fees * fees_multiplier)
                        - buy_cost
                    )

                    # sell fees transaction
                    add_transaction(
                        trading_transactions_history=trading_transactions_history,
                        prev_transaction_id=prev_transaction_id,
                        trade=trade,
                        _type=trading_enums.TransactionType.TRADING_FEE.value,
                        pair=pair,
                        transaction_currency=parsed_symbol.quote,
                        transaction_quantity=-fees * fees_multiplier,
                    )
                    # realized pnl transaction
                    add_transaction(
                        trading_transactions_history=trading_transactions_history,
                        prev_transaction_id=prev_transaction_id,
                        trade=trade,
                        _type=trading_enums.TransactionType.REALIZED_PNL.value,
                        pair=pair,
                        transaction_currency=parsed_symbol.quote,
                        side="long",
                        realized_pnl=local_pnl,
                        closed_quantity=-trade_volume,
                        cumulated_closed_quantity=0,  # todo
                        transaction_first_entry_time=0,  # todo
                        average_entry_price=buy_cost / trade_volume,
                        average_exit_price=trade[commons_enums.PlotAttributes.Y.value],
                        order_exit_price=trade[commons_enums.PlotAttributes.Y.value],
                    )
                else:
                    get_logger().error(f"Unknown trade side: {trade}")
        trading_transactions_history = sorted(
            trading_transactions_history, key=lambda d: d["x"]
        )
        return trading_transactions_history


def add_transaction(
    trading_transactions_history,
    prev_transaction_id,
    trade,
    _type,
    pair,
    transaction_currency,
    transaction_quantity=None,
    side=None,
    realized_pnl=None,
    closed_quantity=None,
    cumulated_closed_quantity=None,
    transaction_first_entry_time=None,
    average_entry_price=None,
    average_exit_price=None,
    order_exit_price=None,
):
    trading_transactions_history.append(
        {
            "x": trade["x"],
            "type": _type,
            "id": prev_transaction_id,
            "symbol": pair,
            "trading_mode": trade["trading_mode"],
            "currency": transaction_currency,
            "quantity": transaction_quantity,
            "order_id": trade["id"],
            "funding_rate": None,
            "realized_pnl": realized_pnl,
            "transaction_fee": None,
            "closed_quantity": closed_quantity,
            "cumulated_closed_quantity": cumulated_closed_quantity,
            "first_entry_time": transaction_first_entry_time,
            "average_entry_price": average_entry_price,
            "average_exit_price": average_exit_price,
            "order_exit_price": order_exit_price,
            "leverage": 0,
            "trigger_source": None,
            "side": side,
            "y": 0,
            "chart": "main-chart",
            "kind": "scattergl",
            "mode": "markers",
        }
    )
    prev_transaction_id += 1


def get_logger(_=None):
    return octobot_commons.logging.get_logger("RunAnalysisData")


# def _position_factory(symbol, contract_data):
#     # TODO: historical unrealized pnl, maybe find a better solution that this
#     import mock

#     class _TraderMock:
#         def __init__(self):
#             self.exchange_manager = mock.Mock()
#             self.simulate = True

#     contract = trading_exchange_data.FutureContract(
#         symbol,
#         trading_enums.MarginType(contract_data["margin_type"]),
#         trading_enums.FutureContractType(contract_data["contract_type"]),
#     )
#     return trading_personal_data.create_position_from_type(_TraderMock(), contract)


class CandlesLoadingError(Exception):
    """
    raised when unable to load candles
    """

    pass
