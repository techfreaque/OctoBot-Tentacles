import octobot_trading.enums as trading_enums
import octobot_commons.enums as commons_enums
import octobot_commons.databases as databases
import octobot_commons.errors as commons_errors
import tentacles.Meta.Keywords.scripting_library.run_analysis.run_analysis_data as run_analysis_data


def plot_unrealized_portfolio_value(
    run_data: run_analysis_data.RunAnalysisData,
    plotted_element,
    own_yaxis: bool = False,
):
    plotted_element.plot(
        mode="scatter",
        x=run_data.portfolio_value_times,
        y=run_data.portfolio_values,
        title="Unrealized portfolio value",
        own_yaxis=own_yaxis,
    )


async def plot_realized_trade_gains(
    run_data: run_analysis_data.RunAnalysisData,
    plotted_element,
    x_as_trade_count: bool = True,
    own_yaxis: bool = False,
):
    await run_data.load_realized_pnl(x_as_trade_count)
    plotted_element.plot(
        kind="bar",
        x=run_data.realized_pnl_x_data,
        y=run_data.realized_pnl_trade_gains_data,
        x_type="tick0" if x_as_trade_count else "date",
        title="Realized gains per trade",
        own_yaxis=own_yaxis,
    )


async def plot_realized_portfolio_value(
    run_data: run_analysis_data.RunAnalysisData,
    plotted_element,
    x_as_trade_count: bool = True,
    own_yaxis: bool = False,
):
    await run_data.load_realized_pnl(x_as_trade_count)
    plotted_element.plot(
        mode="scatter",
        x=run_data.realized_pnl_x_data,
        y=run_data.realized_pnl_cumulative,
        x_type="tick0" if x_as_trade_count else "date",
        title="Realized portfolio value",
        own_yaxis=own_yaxis,
        line_shape="hv",
    )


async def plot_historical_funding_fees(
    run_data: run_analysis_data.RunAnalysisData,
    plotted_element,
    own_yaxis: bool = True,
):
    await run_data.load_grouped_funding_fees()
    for currency, fees in run_data.funding_fees_history_by_pair.items():
        cumulative_fees = []
        previous_fee = 0
        for fee in fees:
            cumulated_fee = fee["quantity"] + previous_fee
            cumulative_fees.append(cumulated_fee)
            previous_fee = cumulated_fee
        plotted_element.plot(
            mode="scatter",
            x=[fee[commons_enums.PlotAttributes.X.value] for fee in fees],
            y=cumulative_fees,
            title=f"{currency} paid funding fees",
            own_yaxis=own_yaxis,
            line_shape="hv",
        )


def plot_historical_wins_and_losses(
    run_data: run_analysis_data.RunAnalysisData,
    plotted_element,
    x_as_trade_count: bool = False,
    own_yaxis: bool = True,
):
    run_data.generate_wins_and_losses(x_as_trade_count)
    plotted_element.plot(
        mode="scatter",
        x=run_data.wins_and_losses_x_data,
        y=run_data.wins_and_losses_data,
        x_type="tick0" if x_as_trade_count else "date",
        title="wins and losses count",
        own_yaxis=own_yaxis,
        line_shape="hv",
    )


def plot_historical_win_rates(
    run_data: run_analysis_data.RunAnalysisData,
    plotted_element,
    x_as_trade_count: bool = False,
    own_yaxis: bool = True,
):
    run_data.generate_win_rates(x_as_trade_count)
    plotted_element.plot(
        mode="scatter",
        x=run_data.win_rates_x_data,
        y=run_data.win_rates_data,
        x_type="tick0" if x_as_trade_count else "date",
        title="win rate",
        own_yaxis=own_yaxis,
        line_shape="hv",
    )


async def plot_best_case_growth(
    run_data: run_analysis_data.RunAnalysisData,
    plotted_element,
    x_as_trade_count: bool = False,
    own_yaxis: bool = False,
):
    await run_data.get_best_case_growth_from_transactions(
        x_as_trade_count,
    )
    plotted_element.plot(
        mode="scatter",
        x=run_data.best_case_growth_x_data,
        y=run_data.best_case_growth_data,
        x_type="tick0" if x_as_trade_count else "date",
        title="best case growth",
        own_yaxis=own_yaxis,
        line_shape="hv",
    )


def _plot_table_data(
    data,
    plotted_element,
    data_name,
    additional_key_to_label,
    additional_columns,
    datum_columns_callback,
):
    if not data:
        run_analysis_data.get_logger().debug(
            f"Nothing to create a table from when reading {data_name}"
        )
        return
    column_render = _get_default_column_render()
    types = _get_default_types()
    key_to_label = {
        **plotted_element.TABLE_KEY_TO_COLUMN,
        **additional_key_to_label,
    }
    columns = (
        _get_default_columns(plotted_element, data, column_render, key_to_label)
        + additional_columns
    )
    if datum_columns_callback:
        for datum in data:
            datum_columns_callback(datum)
    rows = _get_default_rows(data, columns)
    searches = _get_default_searches(columns, types)
    plotted_element.table(data_name, columns=columns, rows=rows, searches=searches)


async def plot_trades(meta_database, plotted_element):
    data = await meta_database.get_trades_db().all(commons_enums.DBTables.TRADES.value)
    key_to_label = {
        "y": "Price",
        "type": "Type",
        "side": "Side",
    }
    additional_columns = [
        {"field": "total", "label": "Total", "render": None},
        {"field": "fees", "label": "Fees", "render": None},
    ]

    def datum_columns_callback(datum):
        datum["total"] = datum["cost"]
        datum["fees"] = f'{datum["fees_amount"]} {datum["fees_currency"]}'

    _plot_table_data(
        data,
        plotted_element,
        commons_enums.DBTables.TRADES.value,
        key_to_label,
        additional_columns,
        datum_columns_callback,
    )


def plot_metadata(run_data: run_analysis_data.RunAnalysisData):
    with run_data.run_display.part("metadata", "dictionary") as plotted_element:
        plotted_element.dictionary("metadata", dictionary=run_data.metadata)


async def display_withdrawals_table(
    run_data: run_analysis_data.RunAnalysisData, plotted_element
):
    withdrawal_history = await run_data.load_or_generate_transactions(
        transaction_types=(trading_enums.TransactionType.BLOCKCHAIN_WITHDRAWAL.value,)
    )

    # apply quantity to y for each withdrawal
    for withdrawal in withdrawal_history:
        withdrawal["y"] = withdrawal["quantity"]
    key_to_label = {
        "y": "Quantity",
        "currency": "Currency",
        "side": "Side",
    }
    additional_columns = []

    _plot_table_data(
        withdrawal_history,
        plotted_element,
        "Withdrawals",
        key_to_label,
        additional_columns,
        None,
    )


async def plot_positions(run_data: run_analysis_data.RunAnalysisData, plotted_element):
    realized_pnl_history = await run_data.load_or_generate_transactions(
        transaction_types=(
            trading_enums.TransactionType.REALIZED_PNL.value,
            trading_enums.TransactionType.CLOSE_REALIZED_PNL.value,
        )
    )
    key_to_label = {
        "x": "Exit time",
        "first_entry_time": "Entry time",
        "average_entry_price": "Average entry price",
        "average_exit_price": "Average exit price",
        "cumulated_closed_quantity": "Cumulated closed quantity",
        "realised_pnl": "Realised PNL",
        "side": "Side",
        "trigger_source": "Closed by",
    }

    _plot_table_data(
        realized_pnl_history, plotted_element, "Positions", key_to_label, [], None
    )


async def display(plotted_element, label, value):
    plotted_element.value(label, value)


async def display_html(plotted_element, html):
    plotted_element.html_value(html)


async def plot_table(
    meta_database,
    plotted_element,
    data_source,
    columns=None,
    rows=None,
    searches=None,
    column_render=None,
    types=None,
    cache_value=None,
):
    data = []
    if data_source == commons_enums.DBTables.TRADES.value:
        data = await meta_database.get_trades_db().all(
            commons_enums.DBTables.TRADES.value
        )
    elif data_source == commons_enums.DBTables.ORDERS.value:
        data = await meta_database.get_orders_db().all(
            commons_enums.DBTables.ORDERS.value
        )
    else:
        exchange = meta_database.run_dbs_identifier.context.exchange_name
        symbol = meta_database.run_dbs_identifier.context.symbol
        symbol_db = meta_database.get_symbol_db(exchange, symbol)
        if cache_value is None:
            data = await symbol_db.all(data_source)
        else:
            query = (await symbol_db.search()).title == data_source
            cache_data = await symbol_db.select(
                commons_enums.DBTables.CACHE_SOURCE.value, query
            )
            if cache_data:
                try:
                    cache_database = databases.CacheDatabase(
                        cache_data[0][commons_enums.PlotAttributes.VALUE.value]
                    )
                    cache = await cache_database.get_cache()
                    x_shift = cache_data[0]["x_shift"]
                    data = [
                        {
                            "x": (
                                cache_element[
                                    commons_enums.CacheDatabaseColumns.TIMESTAMP.value
                                ]
                                + x_shift
                            )
                            * 1000,
                            "y": cache_element[cache_value],
                        }
                        for cache_element in cache
                    ]
                except KeyError as error:
                    run_analysis_data.get_logger().warning(
                        f"Missing cache values when plotting data: {error}"
                    )
                except commons_errors.DatabaseNotFoundError as error:
                    run_analysis_data.get_logger().warning(
                        f"Missing cache values when plotting data: {error}"
                    )

    if not data:
        run_analysis_data.get_logger().debug(
            f"Nothing to create a table from when reading {data_source}"
        )
        return
    column_render = column_render or _get_default_column_render()
    types = types or _get_default_types()
    columns = columns or _get_default_columns(plotted_element, data, column_render)
    rows = rows or _get_default_rows(data, columns)
    searches = searches or _get_default_searches(columns, types)
    plotted_element.table(data_source, columns=columns, rows=rows, searches=searches)


def _get_default_column_render():
    return {"Time": "datetime", "Entry time": "datetime", "Exit time": "datetime"}


def _get_default_types():
    return {"Time": "datetime", "Entry time": "datetime", "Exit time": "datetime"}


def _get_default_columns(plotted_element, data, column_render, key_to_label=None):
    key_to_label = key_to_label or plotted_element.TABLE_KEY_TO_COLUMN
    return [
        {
            "field": row_key,
            "label": key_to_label[row_key],
            "render": column_render.get(key_to_label[row_key], None),
        }
        for row_key, row_value in data[0].items()
        if row_key in key_to_label and row_value is not None
    ]


def _get_default_rows(data, columns):
    column_fields = set(col["field"] for col in columns)
    return [
        {key: val for key, val in row.items() if key in column_fields} for row in data
    ]


def _get_default_searches(columns, types):
    return [
        {
            "field": col["field"],
            "label": col["label"],
            "type": types.get(col["label"]),
        }
        for col in columns
    ]
