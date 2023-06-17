import datetime
import enum
import time
from ibapi.contract import Contract
import octobot_commons
import octobot_commons.enums as commons_enums
from ibapi import client as ibapi_client
from ibapi import common as ibapi_common
from ibapi import wrapper as ibapi_wrapper
from octobot_commons.symbols.symbol import Symbol
from octobot_commons.symbols.symbol_util import parse_symbol


class IBKRTimeFrames(enum.Enum):
    """
    IBKRTimeFrames supported time frames values
    """

    ONE_MINUTE = "1 min"
    THREE_MINUTES = "3 mins"
    TWO_MINUTES = "2 mins"
    FIVE_MINUTES = "5 mins"
    TEN_MINUTES = "10 mins"
    FIFTEEN_MINUTES = "15 mins"
    TWENTY_MINUTES = "20 mins"
    THIRTY_MINUTES = "30 mins"
    ONE_HOUR = "1 hour"
    TWO_HOURS = "2 hours"
    THREE_HOURS = "3 hours"
    FOUR_HOURS = "4 hours"
    HEIGHT_HOURS = "8 hours"
    ONE_DAY = "1 day"
    ONE_WEEK = "1 week"
    ONE_MONTH = "1 month"


class IbkrWrapper(ibapi_wrapper.EWrapper):
    def historicalData(self, reqId: int, bar: ibapi_common.BarData):
        print("HistoricalData. ReqId:", reqId, "BarData.", bar)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)

    def historicalDataUpdate(self, reqId: int, bar: ibapi_common.BarData):
        print("HistoricalDataUpdate. ReqId:", reqId, "BarData.", bar)

    def symbolSamples(
        self, reqId: int, contractDescriptions: ibapi_common.ListOfContractDescription
    ):
        super().symbolSamples(reqId, contractDescriptions)
        print("Symbol Samples. Request Id: ", reqId)

        for contractDescription in contractDescriptions:
            derivSecTypes = ""
            for derivSecType in contractDescription.derivativeSecTypes:
                derivSecTypes += " "
                derivSecTypes += derivSecType
                print(
                    "Contract: conId:%s, symbol:%s, secType:%s primExchange:%s, "
                    "currency:%s, derivativeSecTypes:%s, description:%s, issuerId:%s"
                    % (
                        contractDescription.contract.conId,
                        contractDescription.contract.symbol,
                        contractDescription.contract.secType,
                        contractDescription.contract.primaryExchange,
                        contractDescription.contract.currency,
                        derivSecTypes,
                        contractDescription.contract.description,
                        contractDescription.contract.issuerId,
                    )
                )


class IBKREchangeClient(ibapi_client.EClient):
    WRAPPER_CLASS: IbkrWrapper = IbkrWrapper
    wrapper: IbkrWrapper

    def __init__(self):
        wrapper = self.WRAPPER_CLASS()
        super().__init__(wrapper)

    name: str = "ibkr"
    symbols: set = {"TSLA/USD:STK-NASDAQ"}
    _TIMEFRAME_MAP = {
        commons_enums.TimeFrames.ONE_MINUTE.value: IBKRTimeFrames.ONE_MINUTE.value,
        commons_enums.TimeFrames.THREE_MINUTES.value: IBKRTimeFrames.THREE_MINUTES.value,
        # commons_enums.TimeFrames.TWO_MINUTES.value: IBKRTimeFrames.TWO_MINUTES.value,
        commons_enums.TimeFrames.FIVE_MINUTES.value: IBKRTimeFrames.FIVE_MINUTES.value,
        # commons_enums.TimeFrames.TEN_MINUTES.value: IBKRTimeFrames.TEN_MINUTES.value,
        commons_enums.TimeFrames.FIFTEEN_MINUTES.value: IBKRTimeFrames.FIFTEEN_MINUTES.value,
        commons_enums.TimeFrames.THIRTY_MINUTES.value: IBKRTimeFrames.THIRTY_MINUTES.value,
        commons_enums.TimeFrames.ONE_HOUR.value: IBKRTimeFrames.ONE_HOUR.value,
        commons_enums.TimeFrames.TWO_HOURS.value: IBKRTimeFrames.TWO_HOURS.value,
        commons_enums.TimeFrames.THREE_HOURS.value: IBKRTimeFrames.THREE_HOURS.value,
        commons_enums.TimeFrames.FOUR_HOURS.value: IBKRTimeFrames.FOUR_HOURS.value,
        commons_enums.TimeFrames.HEIGHT_HOURS.value: IBKRTimeFrames.HEIGHT_HOURS.value,
        commons_enums.TimeFrames.ONE_DAY.value: IBKRTimeFrames.ONE_DAY.value,
        commons_enums.TimeFrames.ONE_WEEK.value: IBKRTimeFrames.ONE_WEEK.value,
        commons_enums.TimeFrames.ONE_MONTH.value: IBKRTimeFrames.ONE_MONTH.value,
    }
    timeframes: set = {
        commons_enums.TimeFrames.ONE_MINUTE.value,
        # commons_enums.TimeFrames.TWO_MINUTES.value,
        commons_enums.TimeFrames.THREE_MINUTES.value,
        commons_enums.TimeFrames.FIVE_MINUTES.value,
        # commons_enums.TimeFrames.TEN_MINUTES.value,
        commons_enums.TimeFrames.FIFTEEN_MINUTES.value,
        commons_enums.TimeFrames.THIRTY_MINUTES.value,
        commons_enums.TimeFrames.ONE_HOUR.value,
        commons_enums.TimeFrames.TWO_HOURS.value,
        commons_enums.TimeFrames.THREE_HOURS.value,
        commons_enums.TimeFrames.FOUR_HOURS.value,
        commons_enums.TimeFrames.HEIGHT_HOURS.value,
        commons_enums.TimeFrames.ONE_DAY.value,
        commons_enums.TimeFrames.ONE_WEEK.value,
        commons_enums.TimeFrames.ONE_MONTH.value,
    }

    def convert_timeframe_to_ibkr_timeframe(self, timeframe: str) -> str:
        return self._TIMEFRAME_MAP[timeframe]

    async def close(self):
        pass

    def setSandboxMode(self, is_sandboxed: bool):
        pass

    async def fetch_balance(self, **params: dict):
        return {}

    async def load_markets(self, reload: bool):
        pass

    @staticmethod
    def milliseconds():
        return time.time() * 1000

    async def fetch_trades(self, symbol: str, limit: int, **params: dict):
        return []

    async def fetch_ohlcv(self, symbol, time_frame: str, limit, since, **params):
        parsed_symbol: Symbol = parse_symbol(symbol)
        contract = Contract()
        contract.symbol = parsed_symbol.base
        contract.currency = parsed_symbol.quote
        type_exchange_str: str = symbol.split(":")[1]
        contract.secType, contract.exchange = type_exchange_str.split("-")
        queryTime = datetime.datetime.utcfromtimestamp(since / 1000).strftime(
            "%Y%m%d-%H:%M:%S"
        )
        self.reqMatchingSymbols(218, "TSLA")
        self.reqHistoricalData(
            4003,
            contract,
            queryTime,
            "10 Y",
            self.convert_timeframe_to_ibkr_timeframe(time_frame),
            "TRADES",
            1,
            1,
            False,
            [],
        )
        return []

    def market(self, symbol: str):
        parsed_symbol: Symbol = parse_symbol(symbol)
        return {
            # "id": "ETHBTC",
            "symbol": symbol,
            "base": parsed_symbol.base,
            "quote": parsed_symbol.quote,
            # "baseId": "ETH",
            # "quoteId": "BTC",
            # "active": True,
            # "type": "spot",
            # "linear": None,
            # "inverse": None,
            # "spot": True,
            # "swap": False,
            # "future": False,
            # "option": False,
            # "margin": False,
            # "contract": False,
            # "contractSize": False,
            # "expiry": False,
            # "expiryDatetime": False,
            # "optionType": False,
            # "strike": False,
            # "settle": False,
            # "settleId": False,
            # "precision": False,
            # "limits": False,
            # "percentage": False,
            # "feeSide": False,
            # "tierBased": False,
            # "taker": False,
            # "maker": False,
            # "lowercaseId": False,
        }
