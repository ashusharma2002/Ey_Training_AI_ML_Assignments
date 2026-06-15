
# Feature Engineering Report

## Recommended Features

1. Lag Features
   - lag_1
   - lag_5
   - lag_10
   - lag_50

2. Rolling Statistics
   - rolling_mean_10
   - rolling_mean_50
   - rolling_std_10
   - rolling_std_50

3. Time Based Features
   - timestamp
   - elapsed_time

4. Differencing Feature
   - signal_difference

## Rationale

Lag features capture temporal dependency.

Rolling statistics capture local trends and variability.

Differencing helps transform a non-stationary series into a stationary one.

Time-based features preserve temporal information.
