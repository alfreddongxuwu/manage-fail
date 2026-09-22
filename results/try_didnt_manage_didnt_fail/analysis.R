#!/usr/bin/env Rscript
for (pkg in c("lme4", "lmerTest")) {
  if (!requireNamespace(pkg, quietly = TRUE)) stop("Missing R package: ", pkg)
}
options(contrasts = c("contr.treatment", "contr.poly"))
script_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
stopifnot(length(script_arg) == 1L)
script_path <- normalizePath(sub("^--file=", "", script_arg), winslash = "/")
project_dir <- dirname(dirname(dirname(script_path)))
input_path <- file.path(project_dir, "results/results_main/main_combined_clean.csv")
output_dir <- dirname(script_path)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
input_md5 <- unname(tools::md5sum(input_path))
canonical_dir <- file.path(project_dir, "results/try_question_order")
protected_paths <- c(input_path,
  list.files(canonical_dir, recursive = TRUE, full.names = TRUE, all.files = TRUE),
  list.files(file.path(project_dir, "RSA/m2_backoff"),
             recursive = TRUE, full.names = TRUE, all.files = TRUE))
protected_hashes <- tools::md5sum(protected_paths)
d <- read.csv(input_path, stringsAsFactors = FALSE, check.names = FALSE)
source_n <- nrow(d)
utterances <- c("didnt_manage", "didnt_fail")
d <- d[d$utterance_id %in% utterances, , drop = FALSE]
d$try <- as.numeric(d$try_rating_01)
d$utterance <- factor(d$utterance_id, levels = utterances)
d$prior <- factor(d$prior, levels = c("low", "high"))
d$qud <- factor(d$qud, levels = c("TRY?", "P?"))
d$item <- factor(d$item, levels = c("package", "photo"))
d$rating_order <- factor(d$rating_order, levels = c("TRY?|P?|NAT", "P?|TRY?|NAT"))
required <- c("try", "utterance", "prior", "qud", "item", "rating_order")
stopifnot(nrow(d) > 0L, !anyNA(d[required]), !anyDuplicated(d$participant_uuid),
          all(is.finite(d$try)), all(d$try >= 0 & d$try <= 1),
          all(abs(d$try - as.numeric(d$try_rating) / 100) < 1e-12),
          all(d$analysis_status == "include"),
          all(table(d$utterance) > 0), all(table(d$item) > 0))
fit_warnings <- fit_messages <- character()
model <- withCallingHandlers(
  lmerTest::lmer(try ~ utterance + prior + qud + rating_order + (1 | item),
                data = d, REML = TRUE, na.action = na.fail),
  warning = function(w) {
    fit_warnings <<- c(fit_warnings, conditionMessage(w))
    invokeRestart("muffleWarning")
  },
  message = function(m) {
    fit_messages <<- c(fit_messages, conditionMessage(m))
    invokeRestart("muffleMessage")
  }
)
model_name <- "try_didnt_manage_didnt_fail_additive_random_item_question_order"
model_formula <- paste(deparse(formula(model)), collapse = " ")
canonical_model <- readRDS(file.path(canonical_dir, "model.rds"))
stopifnot(identical(model_formula,
  paste(deparse(formula(canonical_model)), collapse = " ")))
sm <- summary(model, ddf = "Satterthwaite")
tt <- anova(model, type = 2, ddf = "Satterthwaite")
coefs <- as.data.frame(coef(sm))
names(coefs) <- c("estimate", "se", "df", "t", "p")
coefs$term <- rownames(coefs)
rownames(coefs) <- NULL
coefs$model_name <- model_name
coefs$ci95_low <- coefs$estimate - qt(.975, coefs$df) * coefs$se
coefs$ci95_high <- coefs$estimate + qt(.975, coefs$df) * coefs$se
coefs <- coefs[c("model_name", "term", "estimate", "se", "df", "t", "p",
                 "ci95_low", "ci95_high")]
terms <- data.frame(model_name = model_name, term = rownames(tt),
                    num_df = tt[["NumDF"]], den_df = tt[["DenDF"]],
                    F = tt[["F value"]], p = tt[["Pr(>F)"]], row.names = NULL)

grid <- expand.grid(utterance = utterances, prior = levels(d$prior),
                    qud = levels(d$qud), rating_order = levels(d$rating_order), KEEP.OUT.ATTRS = FALSE,
                    stringsAsFactors = FALSE)
for (nm in c("utterance", "prior", "qud", "rating_order")) {
  grid[[nm]] <- factor(grid[[nm]], levels = levels(d[[nm]]))
}
x <- lme4::getME(model, "X")
gx <- model.matrix(~ utterance + prior + qud + rating_order, grid,
                   contrasts.arg = attr(x, "contrasts"))
gx <- gx[, names(lme4::fixef(model)), drop = FALSE]
prior_L <- colMeans(gx[grid$prior == "high", ]) - colMeans(gx[grid$prior == "low", ])
qud_L <- colMeans(gx[grid$qud == "P?", ]) - colMeans(gx[grid$qud == "TRY?", ])
specs <- list()
add <- function(analysis, family, direction, L) {
  specs[[length(specs) + 1L]] <<- list(
    analysis = analysis, family = family, direction = direction, L = L)
}
add("prior_effect", "contextual_effects", "high - low", prior_L)
add("qud_effect", "contextual_effects", "P? - TRY?", qud_L)
L <- do.call(rbind, lapply(specs, function(s) s$L))
colnames(L) <- names(lme4::fixef(model))
rownames(L) <- vapply(specs, function(s) s$analysis, character(1))
contrasts <- do.call(rbind, lapply(seq_along(specs), function(i) {
  s <- specs[[i]]
  r <- lmerTest::contest1D(model, unname(s$L), rhs = 0,
                           ddf = "Satterthwaite", confint = TRUE)
  data.frame(model = model_formula, family = s$family, analysis = s$analysis,
             direction = s$direction, estimate = r[["Estimate"]],
             se = r[["Std. Error"]], df = r[["df"]], t = r[["t value"]],
             p = r[["Pr(>|t|)"]], ci95_low = r[["lower"]],
             ci95_high = r[["upper"]], significant_05 = r[["Pr(>|t|)"]] < .05)
}))
vc <- as.data.frame(lme4::VarCorr(model))
opt <- model@optinfo
conv_messages <- unlist(opt$conv$lme4$messages, use.names = FALSE)
item_var <- vc$vcov[vc$grp == "item"]
resid_var <- sigma(model)^2
fit <- data.frame(
  model_name = model_name, formula = model_formula, n = nobs(model),
  item_levels = nlevels(d$item), fixed_columns = ncol(x), fixed_rank = qr(x)$rank,
  REML = lme4::isREML(model), singular = lme4::isSingular(model, tol = 1e-4),
  singular_tolerance = 1e-4, optimizer = opt$optimizer,
  optimizer_code = paste(opt$conv$opt, collapse = "; "),
  convergence_messages = paste(conv_messages, collapse = "; "),
  warning_count = length(fit_warnings), message_count = length(fit_messages),
  max_abs_gradient = max(abs(opt$derivs$gradient)),
  min_hessian_eigenvalue = min(eigen(opt$derivs$Hessian, symmetric = TRUE)$values),
  item_variance = item_var, item_sd = sqrt(item_var),
  residual_variance = resid_var, residual_sd = sigma(model),
  icc = item_var / (item_var + resid_var)
)
stopifnot(nobs(model) == nrow(d), ncol(x) == 5L, qr(x)$rank == 5L,
          nrow(contrasts) == 2L, !anyDuplicated(contrasts$analysis),
          all(is.finite(as.matrix(contrasts[c("estimate", "se", "df", "t", "p")]))),
          max(abs(contrasts$estimate - drop(L %*% lme4::fixef(model)))) < 1e-12,
          max(abs(contrasts$se - sqrt(diag(L %*% as.matrix(vcov(model)) %*% t(L))))) < 1e-12,
          max(abs(contrasts$p - 2 * pt(abs(contrasts$t), contrasts$df, lower.tail = FALSE))) < 1e-12,
          identical(input_md5, unname(tools::md5sum(input_path))))
saveRDS(model, file.path(output_dir, "model.rds"))
write.csv(coefs, file.path(output_dir, "model_coefficients.csv"), row.names = FALSE)
write.csv(terms, file.path(output_dir, "model_term_tests.csv"), row.names = FALSE)
write.csv(contrasts, file.path(output_dir, "prior_qud_effects.csv"), row.names = FALSE)
write.csv(vc, file.path(output_dir, "model_variance_components.csv"), row.names = FALSE)
write.csv(fit, file.path(output_dir, "model_fit_statistics.csv"), row.names = FALSE)
write.csv(data.frame(analysis = rownames(L), L, row.names = NULL, check.names = FALSE),
          file.path(output_dir, "contrast_weights.csv"), row.names = FALSE)
writeLines(c(paste("Input:", "results/results_main/main_combined_clean.csv"), paste("Input MD5:", input_md5),
             paste("UTC run time:", format(Sys.time(), tz = "UTC", usetz = TRUE)),
              "Subset: utterance_id in {didnt_manage, didnt_fail}; no additional exclusions.",
             capture.output(sessionInfo())), file.path(output_dir, "session_info.txt"))
writeLines(c("Additive TRY mixed-effects model: didn't manage + didn't fail", model_formula,
             "Response: try_rating_01, scale 0-1. Estimation: REML.",
             "Reference levels: didn't manage; low; TRY?; TRY-first (TRY?|P?|NAT). Item: package/photo.",
             "All p-values are unadjusted. Tests use Satterthwaite degrees of freedom.",
             "", capture.output(print(sm, correlation = FALSE)), "",
             capture.output(print(tt)), "", "Requested prior and QUD contrasts:",
             capture.output(print(contrasts, row.names = FALSE)), "",
             "Fit diagnostics:", capture.output(print(fit)), "",
             "Fit warnings:", if (length(fit_warnings)) fit_warnings else "None",
             "Fit messages:", if (length(fit_messages)) fit_messages else "None"),
           file.path(output_dir, "full_model_summary.txt"))

png(file.path(output_dir, "model_diagnostic_plots.png"), width = 1800, height = 1400, res = 180)
par(mfrow = c(2, 2), mar = c(4.5, 4.5, 3, 1))
z <- residuals(model) / sigma(model)
plot(fitted(model), z, xlab = "Conditional fitted TRY", ylab = "Standardized residual",
     main = "Residuals versus fitted", pch = 16, cex = .4, col = "#203D5C70")
abline(h = 0, col = "gray40")
qqnorm(z, main = "Normal Q-Q", pch = 16, cex = .4, col = "#203D5C70")
qqline(z, col = "gray40")
hist(z, breaks = 30, main = "Residual distribution", xlab = "Standardized residual",
     col = "#CCD9E5", border = "white")
boxplot(z ~ d$item, main = "Residuals by item", xlab = "Item",
        ylab = "Standardized residual", col = "#CCD9E5")
dev.off()

fmt_p <- function(p) ifelse(p < .001, formatC(p, format = "e", digits = 3), sprintf("%.5f", p))
term_rows <- vapply(seq_len(nrow(terms)), function(i) {
 r <- terms[i, ]
 sprintf("| %s | %.0f | %.3f | %.4f | %s |", r$term, r$num_df, r$den_df, r$F, fmt_p(r$p))
}, character(1))
contrast_rows <- vapply(seq_len(nrow(contrasts)), function(i) {
 r <- contrasts[i, ]
 sprintf("| %s | %.6f | %.6f | %.3f | %.3f | %s | [%.6f, %.6f] |",
         r$analysis, r$estimate, r$se, r$df, r$t, fmt_p(r$p), r$ci95_low, r$ci95_high)
}, character(1))
utterance_counts <- as.data.frame(table(utterance = d$utterance))
write.csv(utterance_counts, file.path(output_dir, "utterance_counts.csv"), row.names = FALSE)
design_counts <- as.data.frame(table(utterance = d$utterance, prior = d$prior, qud = d$qud,
                                     rating_order = d$rating_order, item = d$item))
write.csv(design_counts, file.path(output_dir, "design_cell_counts.csv"), row.names = FALSE)
if (!requireNamespace("dplyr", quietly = TRUE)) stop("Missing R package: dplyr")
suppressPackageStartupMessages(library(dplyr))
source(file.path(project_dir, "code/figures/condition_summary.R"))
desc <- equal_condition_summary(d, c("utterance", "prior", "qud"), rating = "try") %>%
  select(utterance, prior, qud, n, mean, sd, se, cells, df) %>%
  as.data.frame()
write.csv(desc, file.path(output_dir, "descriptive_cell_means.csv"), row.names = FALSE)
report <- c("# TRY subset results: didn't manage + didn't fail", "",
 paste("Model:", model_formula), "", paste("N =", nrow(d), "; response scale: 0-1."),
 sprintf("Subset of %d source observations: %s.", source_n,
   paste(sprintf("%s: %d", utterance_counts$utterance, utterance_counts$Freq),
         collapse = "; ")),
 "All included observations for these two utterances are retained; no additional exclusions.",
 "Reference levels: didn't manage, low prior, TRY? QUD, TRY-first.",
 "REML estimation using lmerTest/lme4. Item has package and photo levels.",
 "Prior, QUD and rating-order effects are common additive effects across the two selected utterances.",
 "Rating order compares completion-first (P?|TRY?|NAT) with TRY-first (TRY?|P?|NAT).",
 "Naturalness is always last. The model contains main effects only.",
 "Coefficients and planned contrasts use two-sided Wald-type t-tests with Satterthwaite df.",
 "Overall terms use Type II F-tests with Satterthwaite denominator df. All p-values are unadjusted.",
 "There are no interactions; separate contextual slopes for each utterance are not estimated or tested. The 95% CIs use the same t distribution.", "",
 "## Fit", "", paste("- Singular fit at tolerance 1e-4:", fit$singular),
 paste("- Fixed design rank:", fit$fixed_rank, "of", fit$fixed_columns),
 paste("- Optimizer code:", fit$optimizer_code),
 paste("- Fit warnings:", fit$warning_count),
 paste("- Convergence messages:", if (length(conv_messages)) paste(conv_messages, collapse = "; ") else "none"),
 sprintf("- Item variance: %.8f; SD: %.6f; ICC: %.6f.", item_var, sqrt(item_var), fit$icc),
 "- The two item levels provide limited information about the random-intercept variance.", "",
 "## Overall fixed effects", "", "| Term | NumDF | DenDF | F | p |",
 "|---|---:|---:|---:|---:|", term_rows, "",
 "## Prior and QUD effects", "", "| Analysis | Estimate | SE | df | t | p | 95% CI |",
 "|---|---:|---:|---:|---:|---:|---|", contrast_rows, "",
 "The contextual coefficients are shared across the two selected utterances under the additive model.",
 "This supplementary subset analysis leaves the canonical full-sample analysis unchanged.", "",
 "Reproduce with Rscript --vanilla results/try_didnt_manage_didnt_fail/analysis.R; requires lme4, lmerTest and dplyr.")
writeLines(report, file.path(output_dir, "RESULTS_SUMMARY.md"))
cat(paste(report, collapse = "\n"), "\n")



effect_terms <- terms[match(c("prior", "qud"), terms$term), ]
effect_coefs <- coefs[match(c("priorhigh", "qudP?"), coefs$term), ]
stopifnot(all(effect_terms$num_df == 1),
          max(abs(effect_terms$F - contrasts$t^2)) < 1e-8,
          max(abs(effect_terms$p - contrasts$p)) < 1e-10,
          max(abs(effect_coefs$p - contrasts$p)) < 1e-10,
          sum(utterance_counts$Freq) == nrow(d),
          sum(design_counts$Freq) == nrow(d))
saved <- readRDS(file.path(output_dir, "model.rds"))
stopifnot(inherits(saved, "lmerModLmerTest"),
          identical(formula(saved), formula(model)),
          nobs(saved) == nrow(d),
          identical(lme4::fixef(saved), lme4::fixef(model)),
          identical(protected_hashes, tools::md5sum(protected_paths)))
writeLines(c("PASS: only the two selected utterances are included, retaining all their eligible observations.",
             "PASS: formula matches canonical model; fixed design rank 5/5; two contextual contrasts.",
             "PASS: contrast estimates, SEs and unadjusted two-sided t p-values match matrix calculations.",
             "PASS: prior/QUD coefficients, contrasts and 1-df Type II F tests agree.",
             "PASS: saved model has the expected class, formula, sample size and coefficients.",
             "PASS: source data, canonical full-sample analysis and original RSA backoff files are unchanged."),
           file.path(output_dir, "validation.txt"))
writeLines(c("# Supplementary TRY analysis", "",
  "Subset: didnt_manage and didnt_fail. See RESULTS_SUMMARY.md for estimates and diagnostics.", "",
  "Run after the main mixed model and RSA models:", "",
  "Rscript --vanilla results/try_didnt_manage_didnt_fail/analysis.R"),
  file.path(output_dir, "README.md"))
cat("\nSubset analysis validation passed.\n")
