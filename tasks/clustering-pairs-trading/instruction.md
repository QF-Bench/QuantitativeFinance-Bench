# Screen equity pairs using clustering and cointegration

Use the supplied daily close-price panel at `/app/sp500_prices.csv` to compare three ways of grouping similar stocks and to screen for cointegrated price pairs within affinity-propagation clusters. This is an exploratory in-sample screen. The 5% cutoff is per regression, with no multiple-testing adjustment. The results do not establish future trading profitability.

## Data and features

Use the Date column as the chronological index. Preserve the input ticker-column order when fitting models. Drop tickers with more than 30% missing prices, forward-fill within each remaining ticker, then back-fill initial missing prices. Use daily simple returns, excluding the first undefined return. Annual return is the arithmetic daily mean times 252; annual volatility is the sample standard deviation (ddof=1) times sqrt(252). These are annualized sample descriptors, not realized compound annual growth rates. Standardize each feature across tickers with StandardScaler defaults. Use columns in (annual return, annual volatility) order. For a reproducible baseline, round the standardized values to 10 decimal places with `X = np.ascontiguousarray(np.round(X, 10), dtype=np.float64)`. Use that matrix for Ward and affinity propagation. Run the numerical fits with a single thread. Export annual return and volatility before standardization or rounding.

For the KMeans sweep, choose either the same rounded matrix or a full-precision matrix reconstructed from your exported features. For the full-precision option, write the raw annual features with round-trip float64 precision, reload them with `pd.read_csv(..., float_precision="round_trip")`, and apply `StandardScaler().fit_transform(np.asfortranarray(frame[["annual_return", "annual_volatility"]], dtype=np.float64))`. Use your chosen matrix for **all** KMeans fits, inertias, silhouettes, and the winning partition. Tiny floating-point differences can select different local minima. Each complete reproducible sweep is valid.

## Cluster models

On these two standardized features, compare:

- KMeans for every integer k from 2 through 19 with random_state=10, n_init=10, and the other defaults in the supplied environment. Record inertia and the Euclidean silhouette for every k. Use the k with the highest full-precision silhouette (smallest k in an exact tie).
- AgglomerativeClustering with four clusters, Euclidean distance and Ward linkage.
- AffinityPropagation with random_state=10 and all other defaults. Use the fitted labels and center indices.

For each model, number the clusters from 0 in alphabetical order of their smallest member ticker. This is a naming convention; the numerical labels returned by the libraries have no intrinsic meaning. Record the mean silhouette of each fitted partition and the name of the model with the largest silhouette. Use affinity propagation for pair screening regardless of which model maximizes silhouette.

## Pair screen

For every unordered pair of distinct tickers in the same affinity-propagation cluster, compare their cleaned **price levels**. Put the alphabetically earlier ticker first and use it as the dependent variable in `statsmodels.tsa.stattools.coint(first, second, trend="c", maxlag=None, autolag="aic")`. Test each pair once. A p-value strictly less than 0.05 passes the in-sample screen. The interpretation assumes the price levels are I(1); you need not pretest integration order or claim that each stock satisfies it.

## Output

Write all files in `OUTPUT_DIR` (default `/app/output`). Use the names `kmeans`, `hierarchical`, and `affinity_propagation`. Use finite numbers with at least eight significant digits except where four decimals are requested.

- `features.csv`: columns `ticker,annual_return,annual_volatility,kmeans,hierarchical,affinity_propagation,ap_exemplar`. One row per retained ticker in input order. The final field is its affinity-propagation exemplar's ticker.
- `kmeans_sweep.csv`: `k,inertia,silhouette_score`, one row per k in ascending order.
- `pair_tests.csv`: `ticker1,ticker2,cluster,pvalue`, one row per regression, sorted by (cluster,ticker1,ticker2). `pairs.csv` contains the passing subset in the same order with columns `ticker1,ticker2,cluster`.
- `cluster_summary.csv`: `cluster,num_stocks,num_pairs`, one row for each cluster with at least one passing pair in ascending cluster order. Count all cluster members in num_stocks.
- `silhouette_scores.csv`: `method,n_clusters,silhouette_score`, one row per model. Round these three silhouette scores to four decimals.
- `results.json` with objects:
  - `data_cleaning`: integer fields `original_tickers,dropped_tickers,final_tickers,trading_days`. Count columns, dropped columns, retained columns and dates respectively.
  - `clustering`: one object per model containing `n_clusters` and its four-decimal `silhouette_score`, plus strings `best_method` (highest unrounded silhouette) and `selected_method` (the pair-screening model).
  - `pair_selection`: integer fields `total_pairs,unique_tickers_in_pairs,clusters_evaluated,total_tests_performed`. Count passing pairs, their distinct tickers, nonsingleton clusters, and all regressions respectively.
- Invoke the public presentation helper `python /app/plot_clusters.py OUTPUT_DIRECTORY` on your completed CSV files. It draws the elbow and silhouette sweep, three cluster scatters, Ward dendrogram, affinity exemplars and size bars, and a t-SNE view of passing pairs. It computes display coordinates for the trees and t-SNE using the supplied feature table. Submit the eight PNG files it generates. The helper standardizes displayed feature axes and fixes visual conventions; generating the quantitative tables is your responsibility.
