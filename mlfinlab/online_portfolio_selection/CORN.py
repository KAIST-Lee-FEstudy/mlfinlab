from mlfinlab.online_portfolio_selection.olps_utils import *
import cvxpy as cp
from mlfinlab.online_portfolio_selection.OLPS import OLPS


class CORN(OLPS):
    """
    This class implements the Correlation Driven Nonparametric Learning strategy.
    """

    def __init__(self, window=20, rho=.6):
        """
        Constructor.
        """
        super().__init__()
        self.window = window
        self.rho = rho
        self.corr_coef = None


    # I didn't really need to rewrite this method but I did it anyways
    # because I thought self.corr_coef might take a long time
    # will look for a coding style that might not require that
    def run(self, _weights, _relative_return):
        # set initial weights
        self.weights = self.first_weight(_weights)
        self.all_weights[0] = self.weights

        # rolling correlation coefficient
        self.corr_coef = self.calculate_rolling_correlation_coefficient(_relative_return)

        # Run the Algorithm for the rest of data
        for t in range(1, self.final_number_of_time):
            # update weights
            self.weights = self.update_weight(self.weights, _relative_return, t)
            self.all_weights[t] = self.weights

    def update_weight(self, _weights, _relative_return, _time):
        similar_set = []
        new_weights = self.uniform_weight(self.number_of_assets)

        if _time - 1 > self.window:
            for i in range(self.window + 1, _time - 1):
                if self.corr_coef[i - 1][_time - 1] > self.rho:
                    similar_set.append(i)
            if similar_set:
                similar_sequences = _relative_return[similar_set]
                new_weights = self.optimize(similar_sequences)
        return new_weights

    # optimize the weight that maximizes the returns
    def optimize(self, _optimize_array):
        length_of_time = _optimize_array.shape[0]
        number_of_assets = _optimize_array.shape[1]
        if length_of_time == 1:
            best_idx = np.argmax(_optimize_array)
            weight = np.zeros(number_of_assets)
            weight[best_idx] = 1
            return weight

        # initialize weights
        weights = cp.Variable(self.number_of_assets)

        # used cp.log and cp.sum to make the cost function a convex function
        # multiplying continuous returns equates to summing over the log returns
        portfolio_return = cp.sum(cp.log(_optimize_array * weights))

        # Optimization objective and constraints
        allocation_objective = cp.Maximize(portfolio_return)
        allocation_constraints = [
                cp.sum(weights) == 1,
                weights <= 1,
                weights >= 0
        ]
        # Define and solve the problem
        problem = cp.Problem(
                objective=allocation_objective,
                constraints=allocation_constraints
        )
        problem.solve(solver=cp.SCS)
        return weights.value


def main():
    stock_price = pd.read_csv("../tests/test_data/stock_prices.csv", parse_dates=True, index_col='Date')
    stock_price = stock_price.dropna(axis=1)
    corn = CORN()
    corn.allocate(stock_price, resample_by='w')
    print(corn.all_weights)
    print(corn.portfolio_return)
    corn.portfolio_return.plot()


if __name__ == "__main__":
    main()