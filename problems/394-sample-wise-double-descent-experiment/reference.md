# Reference discussion

This API and experimental protocol are practice reconstruction choices. The runnable reference is `tests/reference_solutions/sample_wise_double_descent_experiment.py`.

The hypothesis is that label noise can be amplified near the interpolation threshold when sample count crosses a fixed feature dimension. We fix the teacher, feature distribution, feature dimension, noise scale, and seed grid. Within each seed we use nested training prefixes and a shared independent heldout set for every estimator. A seed changes both the training and heldout realization: the reported spread therefore includes both sources of variability. It is population standard deviation across these runs, not a confidence interval or standard error.

For the prompt's four-seed example (dimension 12, 128 heldout samples), rounded heldout mean MSEs are:

| Samples | Noisy minimum norm | Noisy ridge 0.001 | Noisy ridge 0.1 | Noisy ridge 1.0 | Noiseless minimum norm |
| --- | --- | --- | --- | --- | --- |
| 4 | 1.0184 | 1.0181 | 0.9963 | 1.0431 | 0.6479 |
| 8 | 0.9577 | 0.9542 | 0.8511 | 0.9919 | 0.4249 |
| 11 | 2.9000 | 1.9611 | 0.7475 | 0.9286 | 0.2195 |
| 12 | 34.7479 | 1.8999 | 0.7630 | 0.9059 | approximately 0 |
| 13 | 3.7746 | 1.6282 | 0.7693 | 0.9128 | approximately 0 |
| 18 | 0.8413 | 0.7932 | 0.5707 | 0.8460 | approximately 0 |
| 32 | 0.4275 | 0.4256 | 0.3582 | 0.6634 | approximately 0 |

These are observed outputs, not target inequalities. At 12 samples, noisy minimum-norm heldout MSE has standard deviation about 51.6790; its large mean is not a stable estimate from only four seeds. The noiseless identifiable model recovers the teacher to numerical precision once the design has full column rank. Below that point, minimum norm interpolates the observed noiseless labels but cannot recover teacher components outside the training row space. Noisy underdetermined and square fits also interpolate training labels, while their heldout errors can remain large.

Writing `X = U diag(s) V.T`, minimum norm multiplies identifiable target components by `1/s`. Small singular values amplify noise. Ridge replaces this with `s / (s**2 + n*lambda)` because the objective uses mean residual loss. Omitting `n` would instead hold the penalty against a sum of residuals fixed, changing the effective regularization as sample size changes. The outputs exclude the penalty from the reported training MSE. Ridge can suppress variance while adding bias; a large penalty can be harmful, as seen for lambda 1.0 at 32 samples compared with lambda 0.1.

Use float64 and a stable least-squares/SVD solve. The reference uses augmented least squares for ridge, with rows `sqrt(n)*sqrt(lambda)*I`; splitting the square roots avoids overflow of the intermediate `n*lambda` for extremely large finite penalties. A direct Gram solve is allowed but squares the design's condition number. Finite precision and `rcond` determine numerical rank; tiny positive penalties may be indistinguishable from zero, and very large ones effectively yield a zero predictor. Near singularity, mathematical error amplification and numerical solver error are different effects. Inspect singular values and residuals before attributing unusual results to either one.

A single finite realization need not have a visible peak, and ridge need not improve every seed or every sample size. Finite heldout size and a small seed set limit conclusions. A next experiment would extend the seed grid in separate bounded batches while retaining raw outcomes and reporting medians/quantiles alongside mean and spread. Keep the sample grid fixed across those controls; changing its maximum changes downstream random draws under this generator. Use a separate validation protocol to select lambda before claiming performance on an untouched final test set.
