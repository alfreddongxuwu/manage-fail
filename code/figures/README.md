# Figures

Requires R packages readr, dplyr, ggplot2, gtable and patchwork, with Cairo support. Run after the statistical and RSA analyses:

```sh
Rscript code/figures/plot_fig2_try_inference.R
Rscript code/figures/plot_fig3_effects.R
Rscript code/figures/plot_fig4_attempt_rsa_comparison.R
```

PDFs are written to `figures/`. Descriptive intervals use condition means and Welch-Satterthwaite degrees of freedom. Figure 1 contains example experiment screens.
