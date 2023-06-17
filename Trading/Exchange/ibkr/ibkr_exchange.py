from octobot_trading import exchanges
from tentacles.Trading.Exchange.ibkr.connector.ibkr_connector import (
    IBKRExchangeConnector,
)


class ibkr(exchanges.RestExchange):
    DEFAULT_CONNECTOR_CLASS = IBKRExchangeConnector

    @classmethod
    def get_name(cls) -> str:
        return "ibkr"

    @classmethod
    def is_supporting_exchange(cls, exchange_candidate_name) -> bool:
        return cls.get_name() == exchange_candidate_name

    async def initialize_impl(self):
        await self.connector.initialize()
        self.symbols = self.connector.symbols
        self.time_frames = self.connector.time_frames

    @classmethod
    def init_user_inputs(cls, inputs: dict) -> None:
        """
        Called at constructor, should define all the exchange's user inputs.
        """

    @classmethod
    def is_configurable(cls):
        return True

    async def stop(self) -> None:
        await self.connector.stop()
        self.exchange_manager = None

    def get_default_type(self):
        return "spot"
