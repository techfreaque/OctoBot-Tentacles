#  Drakkar-Software OctoBot
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
import octobot_commons.logging as logging
import octobot_trading.modes as modes
import octobot_trading.enums as trading_enums


class ScriptedTradingMode(modes.AbstractScriptedTradingMode):

    def __init__(self, config, exchange_manager):
        super().__init__(config, exchange_manager)
        if exchange_manager:
            try:
                import backtesting_script
                self.register_script_module(backtesting_script, live=False)
            except (AttributeError, ModuleNotFoundError):
                pass
            try:
                import profile_trading_script
                self.register_script_module(profile_trading_script)
            except (AttributeError, ModuleNotFoundError):
                pass
        else:
            logging.get_logger(self.get_name()).error(
                "At least one exchange must be enabled to use ScriptedTradingMode"
                )

    @classmethod
    def get_supported_exchange_types(cls) -> list:
        """
        :return: The list of supported exchange types
        """
        return [
            trading_enums.ExchangeTypes.SPOT,
            trading_enums.ExchangeTypes.FUTURE,
        ]
