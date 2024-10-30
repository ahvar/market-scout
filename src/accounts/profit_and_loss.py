import pandas as pd
from src.utils.references import (
    Frequency,
    DAILY_PRICE_FREQ,
    from_config_frequency_pandas_resample,
    arg_not_supplied,
    SECONDS_IN_YEAR,
    ROOT_BDAYS_INYEAR,
    curve_types,
    NET_CURVE,
    GROSS_CURVE,
    COSTS_CURVE,
)
from src.models.vol import robust_daily_vol_given_price
from src.utils.command.command_exceptions import MissingData


class ProfitAndLoss:
    def __init__(
        self,
        price: pd.Series,
        positions: pd.Series,
        fx: pd.Series,
        capital: pd.Series,
        value_per_point: float,  # = 1.0,
        roundpositions: bool,  # init False
        delayfill: bool,  # init False
        passed_diagnostic_df: pd.DataFrame,
    ):
        self._price = price
        self._positions = positions
        self._fx = fx
        self._capital = capital
        self._value_per_point = value_per_point
        self._passed_diagnostic_df = passed_diagnostic_df
        self._delayfill = delayfill
        self._roundpositions = roundpositions

    def calculations_and_diagnostic_df(self) -> pd.DataFrame:
        diagnostic_df = self.passed_diagnostic_df
        calculations = self.calculations_df()
        calculations_and_diagnostic_df = pd.concat(
            [diagnostic_df, calculations], axis=1
        )  ## no ffill

        return calculations_and_diagnostic_df

    def calculations_df(self) -> pd.Series:
        raise NotImplementedError("Not implemented")

    def weight(self, weight: pd.Series):
        weighted_capital = apply_weighting(weight, self.capital)
        weighted_positions = apply_weighting(weight, self.positions)

        return ProfitAndLoss(
            self.price,
            positions=weighted_positions,
            fx=self.fx,
            capital=weighted_capital,
            value_per_point=self.value_per_point,
            roundpositions=self.roundpositions,
            delayfill=self.delayfill,
            passed_diagnostic_df=self._passed_diagnostic_df,
        )

    def capital_as_pd_series_for_frequency(
        self, frequency: Frequency = DAILY_PRICE_FREQ
    ) -> pd.Series:
        capital = self.capital
        resample_freq = from_config_frequency_pandas_resample(frequency)
        capital_at_frequency = capital.resample(resample_freq).ffill()

        return capital_at_frequency

    def as_pd_series_for_frequency(
        self, frequency: Frequency = DAILY_PRICE_FREQ, **kwargs
    ) -> pd.Series:
        as_pd_series = self.as_pd_series(**kwargs)

        ## FIXME: Ugly to get pandas 2.x working
        as_pd_series.index = pd.to_datetime(as_pd_series.index)

        resample_freq = from_config_frequency_pandas_resample(frequency)
        pd_series_at_frequency = as_pd_series.resample(resample_freq).sum()

        return pd_series_at_frequency

    def as_pd_series(self, percent=False):
        if percent:
            return self.percentage_pandl()
        else:
            return self.pandl_in_base_currency()

    def percentage_pandl(self) -> pd.Series:
        pandl_in_base = self.pandl_in_base_currency()

        pandl = self._percentage_pandl_given_pandl(pandl_in_base)

        return pandl

    def _percentage_pandl_given_pandl(self, pandl_in_base: pd.Series):
        capital = self.capital
        if type(capital) is pd.Series:
            capital_aligned = capital.reindex(pandl_in_base.index, method="ffill")
        elif type(capital) is float or type(capital) is int:
            capital_aligned = capital

        return 100.0 * pandl_in_base / capital_aligned

    def pandl_in_base_currency(self) -> pd.Series:
        pandl_in_ccy = self.pandl_in_instrument_currency()
        pandl_in_base = self._base_pandl_given_currency_pandl(pandl_in_ccy)

        return pandl_in_base

    def _base_pandl_given_currency_pandl(self, pandl_in_ccy) -> pd.Series:
        fx = self.fx
        fx_aligned = fx.reindex(pandl_in_ccy.index, method="ffill")

        return pandl_in_ccy * fx_aligned

    def pandl_in_instrument_currency(self) -> pd.Series:
        pandl_in_points = self.pandl_in_points()
        pandl_in_ccy = self._pandl_in_instrument_ccy_given_points_pandl(pandl_in_points)

        return pandl_in_ccy

    def _pandl_in_instrument_ccy_given_points_pandl(
        self, pandl_in_points: pd.Series
    ) -> pd.Series:
        point_size = self.value_per_point

        return pandl_in_points * point_size

    def pandl_in_points(self) -> pd.Series:
        # print(f"positions: \n{self.positions}")
        # print(self.positions.describe())
        # print(f"prices: \n{self.price}")
        # print(self.price.describe())
        pandl_in_points = calculate_pandl(positions=self.positions, prices=self.price)
        return pandl_in_points

    @property
    def price(self) -> pd.Series:
        return self._price

    @property
    def length_in_months(self) -> int:
        positions_monthly = self.positions.resample("1M").last()
        positions_ffill = positions_monthly.ffill()
        positions_no_nans = positions_ffill.dropna()

        return len(positions_no_nans.index)

    @property
    def positions(self) -> pd.Series:
        positions = self._get_passed_positions()
        if positions is arg_not_supplied:
            return arg_not_supplied

        positions_to_use = self._process_positions(positions)

        return positions_to_use

    def _process_positions(self, positions: pd.Series) -> pd.Series:
        if self.delayfill:
            positions_to_use = positions.shift(1)
        else:
            positions_to_use = positions

        if self.roundpositions:
            positions_to_use = positions_to_use.round()

        return positions_to_use

    def _get_passed_positions(self) -> pd.Series:
        positions = self._positions

        return positions

    @property
    def delayfill(self) -> bool:
        return self._delayfill

    @property
    def roundpositions(self) -> bool:
        return self._roundpositions

    @property
    def value_per_point(self) -> float:
        return self._value_per_point

    @property
    def passed_diagnostic_df(self) -> pd.DataFrame:
        diagnostic_df = self._passed_diagnostic_df
        if diagnostic_df is arg_not_supplied:
            return self._default_diagnostic_df
        return diagnostic_df

    @property
    def _default_diagnostic_df(self) -> pd.DataFrame:
        diagnostic_df = pd.DataFrame(dict(price=self.price))
        return diagnostic_df

    @property
    def fx(self) -> pd.Series:
        fx = self._fx
        if fx is arg_not_supplied:
            price_index = self.price.index
            fx = pd.Series([1.0] * len(price_index), price_index)

        return fx

    @property
    def capital(self) -> pd.Series:
        capital = self._capital
        if capital is arg_not_supplied:
            capital = 1.0

        if type(capital) is float or type(capital) is int:
            align_index = self._index_to_align_capital_to
            capital = pd.Series([capital] * len(align_index), align_index)

        return capital

    @property
    def _index_to_align_capital_to(self):
        return self.price.index


def apply_weighting(weight: pd.Series, thing_to_weight: pd.Series) -> pd.Series:
    aligned_weight = weight.reindex(thing_to_weight.index).ffill()
    weighted_thing = thing_to_weight * aligned_weight

    return weighted_thing


def calculate_pandl(positions: pd.Series, prices: pd.Series):
    pos_series = positions.groupby(positions.index).last()
    both_series = pd.concat([pos_series, prices], axis=1)
    both_series.columns = ["positions", "prices"]
    both_series = both_series.ffill()

    price_returns = both_series.prices.diff()

    returns = both_series.positions.shift(1) * price_returns
    returns[returns.isna()] = 0.0

    return returns


class ProfitAndLossWithGenericCosts(ProfitAndLoss):
    def weight(self, weight: pd.Series):
        weighted_capital = apply_weighting(weight, self.capital)
        weighted_positions = apply_weighting(weight, self.positions)

        return ProfitAndLossWithGenericCosts(
            self.price,
            positions=weighted_positions,
            fx=self.fx,
            capital=weighted_capital,
            value_per_point=self.value_per_point,
            roundpositions=self.roundpositions,
            delayfill=self.delayfill,
            passed_diagnostic_df=None,
        )

    def as_pd_series(self, percent=False, curve_type=NET_CURVE):
        if curve_type == NET_CURVE:
            if percent:
                return self.net_percentage_pandl()
            else:
                return self.net_pandl_in_base_currency()

        elif curve_type == GROSS_CURVE:
            if percent:
                return self.percentage_pandl()
            else:
                return self.pandl_in_base_currency()
        elif curve_type == COSTS_CURVE:
            if percent:
                return self.costs_percentage_pandl()
            else:
                return self.costs_pandl_in_base_currency()

        else:
            raise Exception(
                "Curve type %s not recognised! Must be one of %s"
                % (curve_type, curve_types)
            )

    def net_percentage_pandl(self) -> pd.Series:
        gross = self.percentage_pandl()
        costs = self.costs_percentage_pandl()
        net = _add_gross_and_costs(gross, costs)

        return net

    def net_pandl_in_base_currency(self) -> pd.Series:
        gross = self.pandl_in_base_currency()
        costs = self.costs_pandl_in_base_currency()
        net = _add_gross_and_costs(gross, costs)

        return net

    def net_pandl_in_instrument_currency(self) -> pd.Series:
        gross = self.pandl_in_instrument_currency()
        costs = self.costs_pandl_in_instrument_currency()
        net = _add_gross_and_costs(gross, costs)

        return net

    def net_pandl_in_points(self) -> pd.Series:
        gross = self.pandl_in_points()
        costs = self.costs_pandl_in_points()
        net = _add_gross_and_costs(gross, costs)

        return net

    def costs_percentage_pandl(self) -> pd.Series:
        costs_in_base = self.costs_pandl_in_base_currency()
        costs = self._percentage_pandl_given_pandl(costs_in_base)

        return costs

    def costs_pandl_in_base_currency(self) -> pd.Series:
        costs_in_instr_ccy = self.costs_pandl_in_instrument_currency()
        costs_in_base = self._base_pandl_given_currency_pandl(costs_in_instr_ccy)

        return costs_in_base

    def costs_pandl_in_instrument_currency(self) -> pd.Series:
        costs_in_points = self.costs_pandl_in_points()
        costs_in_instr_ccy = self._pandl_in_instrument_ccy_given_points_pandl(
            costs_in_points
        )

        return costs_in_instr_ccy

    def costs_pandl_in_points(self) -> pd.Series:
        raise NotImplementedError


def _add_gross_and_costs(gross: pd.Series, costs: pd.Series):
    net = gross.add(costs, fill_value=0)

    return net


class ProfitAndLossWithSharpeRatioCosts(ProfitAndLossWithGenericCosts):
    def __init__(
        self,
        *args,
        SR_cost: float,
        average_position: pd.Series,
        daily_returns_volatility: pd.Series = arg_not_supplied,
        **kwargs,
    ):
        ## Is SR_cost a negative number?
        super().__init__(*args, **kwargs)
        self._SR_cost = SR_cost
        self._daily_returns_volatility = daily_returns_volatility
        self._average_position = average_position

    def weight(self, weight: pd.Series):
        ## we don't weight fills, instead will be inferred from positions
        weighted_capital = apply_weighting(weight, self.capital)
        weighted_positions = apply_weighting(weight, self.positions)
        weighted_average_position = apply_weighting(weight, self.average_position)

        return ProfitAndLossWithSharpeRatioCosts(
            positions=weighted_positions,
            capital=weighted_capital,
            average_position=weighted_average_position,
            price=self.price,
            fx=self.fx,
            SR_cost=self._SR_cost,
            daily_returns_volatility=self.daily_returns_volatility,
            value_per_point=self.value_per_point,
            roundpositions=self.roundpositions,
            delayfill=self.delayfill,
        )

    def costs_pandl_in_points(self) -> pd.Series:
        SR_cost_as_annualised_figure = self.SR_cost_as_annualised_figure_points()

        position = self.positions
        price = self.price

        SR_cost_per_period = (
            calculate_SR_cost_per_period_of_position_data_match_price_index(
                position,
                price=price,
                SR_cost_as_annualised_figure=SR_cost_as_annualised_figure,
            )
        )

        return SR_cost_per_period

    def SR_cost_as_annualised_figure_points(self) -> pd.Series:
        SR_cost_with_minus_sign = -self.SR_cost
        annualised_price_vol_points_for_an_average_position = (
            self.points_vol_of_an_average_position()
        )

        return (
            SR_cost_with_minus_sign
            * annualised_price_vol_points_for_an_average_position
        )

    def points_vol_of_an_average_position(self) -> pd.Series:
        average_position = self.average_position
        annualised_price_vol_points = self.annualised_price_volatility_points()

        average_position_aligned_to_vol = average_position.reindex(
            annualised_price_vol_points.index, method="ffill"
        )

        return average_position_aligned_to_vol * annualised_price_vol_points

    def annualised_price_volatility_points(self) -> pd.Series:
        return self.daily_price_volatility_points * ROOT_BDAYS_INYEAR

    @property
    def daily_price_volatility_points(self) -> pd.Series:
        daily_price_volatility = self.daily_returns_volatility
        if daily_price_volatility is arg_not_supplied:
            daily_price_volatility = robust_daily_vol_given_price(self.price)

        return daily_price_volatility

    @property
    def daily_returns_volatility(self) -> pd.Series:
        return self._daily_returns_volatility

    @property
    def SR_cost(self) -> float:
        return self._SR_cost

    @property
    def average_position(self) -> pd.Series:
        return self._average_position


def spread_out_annualised_return_over_periods(data_as_annual: pd.Series) -> pd.Series:
    """
    >>> import datetime
    >>> d = datetime.datetime
    >>> date_index1 = [d(2000,1,1,23),d(2000,1,2,23),d(2000,1,3,23)]
    >>> s1 = pd.Series([0.365,0.730,0.365], index=date_index1)
    >>> spread_out_annualised_return_over_periods(s1)
    2000-01-01 23:00:00         NaN
    2000-01-02 23:00:00    0.001999
    2000-01-03 23:00:00    0.000999
    dtype: float64
    """
    period_intervals_in_seconds = (
        data_as_annual.index.to_series().diff().dt.total_seconds()
    )
    period_intervals_in_year_fractions = period_intervals_in_seconds / SECONDS_IN_YEAR
    data_per_period = data_as_annual * period_intervals_in_year_fractions

    return data_per_period


def calculate_SR_cost_per_period_of_position_data_match_price_index(
    position: pd.Series, price: pd.Series, SR_cost_as_annualised_figure: pd.Series
) -> pd.Series:
    # only want nans at the start
    position_ffill = position.ffill()

    ## We don't want to lose calculation because of warmup
    SR_cost_aligned_positions = SR_cost_as_annualised_figure.reindex(
        position_ffill.index, method="ffill"
    )
    SR_cost_aligned_positions_backfilled = SR_cost_aligned_positions.bfill()

    # Don't include costs until we start trading
    SR_cost_aligned_positions_when_position_held = SR_cost_aligned_positions_backfilled[
        ~position_ffill.isna()
    ]

    # Actually output in price space to match gross returns
    SR_cost_aligned_to_price = SR_cost_aligned_positions_when_position_held.reindex(
        price.index, method="ffill"
    )

    # These will be annualised figure, make it a small loss every day
    SR_cost_per_period = spread_out_annualised_return_over_periods(
        SR_cost_aligned_to_price
    )

    return SR_cost_per_period
