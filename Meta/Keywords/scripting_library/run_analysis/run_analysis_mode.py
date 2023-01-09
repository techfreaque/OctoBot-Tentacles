import datetime as datetime
import json as json

import tentacles.Meta.Keywords.scripting_library.run_analysis.run_analysis_data as run_analysis_data
import tentacles.Meta.Keywords.scripting_library.run_analysis.run_analysis_plots as run_analysis_plots


async def run_analysis_script(run_data: run_analysis_data.RunAnalysisData):
    for chart_location in {
        run_data.analysis_settings["chart_location_unrealized_portfolio_value"],
        run_data.analysis_settings["chart_location_realized_portfolio_value"],
        run_data.analysis_settings["chart_location_realized_trade_gains"],
        run_data.analysis_settings["chart_location_best_case_growth"],
        run_data.analysis_settings["chart_location_wins_and_losses_count"],
        run_data.analysis_settings["chart_location_win_rate"],
    }:
        with run_data.run_display.part(chart_location) as plotted_element:
            if (
                run_data.analysis_settings["plot_unrealized_portfolio_value"]
                and run_data.analysis_settings[
                    "chart_location_unrealized_portfolio_value"
                ]
            ):
                run_analysis_plots.plot_unrealized_portfolio_value(
                    run_data,
                    plotted_element,
                    own_yaxis=True,
                )
            if (
                run_data.analysis_settings["plot_realized_portfolio_value"]
                and run_data.analysis_settings[
                    "chart_location_realized_portfolio_value"
                ]
            ):
                await run_analysis_plots.plot_realized_portfolio_value(
                    run_data,
                    plotted_element,
                    x_as_trade_count=False,
                    own_yaxis=True,
                )
            if (
                run_data.analysis_settings["plot_realized_trade_gains"]
                and run_data.analysis_settings["chart_location_realized_trade_gains"]
            ):
                await run_analysis_plots.plot_realized_trade_gains(
                    run_data,
                    plotted_element,
                    x_as_trade_count=False,
                    own_yaxis=True,
                )

            if (
                run_data.analysis_settings["plot_best_case_growth"]
                and run_data.analysis_settings["chart_location_best_case_growth"]
            ):
                await run_analysis_plots.plot_best_case_growth(
                    run_data,
                    plotted_element,
                    x_as_trade_count=False,
                    own_yaxis=False,
                )
            if (
                run_data.analysis_settings["plot_funding_fees"]
                and run_data.analysis_settings["chart_location_funding_fees"]
            ):
                await run_analysis_plots.plot_historical_funding_fees(
                    run_data,
                    plotted_element,
                    own_yaxis=True,
                )
            if (
                run_data.analysis_settings["plot_wins_and_losses_count"]
                and run_data.analysis_settings["chart_location_wins_and_losses_count"]
            ):
                run_analysis_plots.plot_historical_wins_and_losses(
                    run_data,
                    plotted_element,
                    own_yaxis=True,
                    x_as_trade_count=False,
                )
            if (
                run_data.analysis_settings["plot_win_rate"]
                and run_data.analysis_settings["chart_location_win_rate"]
            ):
                run_analysis_plots.plot_historical_win_rates(
                    run_data,
                    plotted_element,
                    own_yaxis=True,
                    x_as_trade_count=False,
                )
            # if (
            #     run_data.analysis_settings["plot_withdrawals"]
            #     and run_data.analysis_settings["chart_location_withdrawals"]
            # ):
            #     await run_analysis_plots.plot_withdrawals(run_data, plotted_element)
    with run_data.run_display.part("list-of-trades-part", "table") as part:
        if run_data.analysis_settings["display_trades_and_positions"]:
            await run_analysis_plots.plot_trades(run_data.run_database, part)
            await run_analysis_plots.plot_positions(run_data, part)
        if run_data.analysis_settings["display_withdrawals_table"]:
            await run_analysis_plots.display_withdrawals_table(run_data, plotted_element)
    run_analysis_plots.plot_metadata(run_data)
    # await plot_table(run_data, part, "SMA 1")  # plot any cache key as a table
    return run_data.run_display
