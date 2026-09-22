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
d <- read.csv(input_path, stringsAsFactors = FALSE, check.names = FALSE)
utterances <- c("managed", "didnt_manage", "failed", "didnt_fail",
                "did", "didnt", "tried", "didnt_try")
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
model_name <- "try_additive_random_item_question_order"
model_formula <- paste(deparse(formula(model)), collapse = " ")
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
cell_x <- t(vapply(utterances, function(u) {
  colMeans(gx[grid$utterance == u, , drop = FALSE])
}, numeric(ncol(gx))))
colnames(cell_x) <- colnames(gx)
prior_L <- colMeans(gx[grid$prior == "high", ]) - colMeans(gx[grid$prior == "low", ])
qud_L <- colMeans(gx[grid$qud == "P?", ]) - colMeans(gx[grid$qud == "TRY?", ])
order_L <- colMeans(gx[grid$rating_order == "P?|TRY?|NAT", ]) -
  colMeans(gx[grid$rating_order == "TRY?|P?|NAT", ])
weight <- function(values) {
  w <- setNames(numeric(length(utterances)), utterances)
  stopifnot(all(names(values) %in% utterances))
  w[names(values)] <- values
  stopifnot(abs(sum(w)) < 1e-12)
  drop(w %*% cell_x)
}
specs <- list()
add <- function(analysis, family, direction, L) {
  specs[[length(specs) + 1L]] <<- list(
    analysis = analysis, family = family, direction = direction, L = L)
}
add("prior_effect", "contextual_effects", "high - low", prior_L)
add("qud_effect", "contextual_effects", "P? - TRY?", qud_L)
add("rating_order_effect", "question_order", "completion-first - TRY-first", order_L)
add("prior_minus_qud_effect", "contextual_cue_comparison",
    "(high - low prior) - (P? - TRY? QUD)", prior_L - qud_L)
add("implicative_boost_all_four_vs_did_and_didnt", "implicative_boost_overall",
    "mean(managed, didnt_manage, failed, didnt_fail) - mean(did, didnt)",
    weight(c(managed = .25, didnt_manage = .25, failed = .25,
             didnt_fail = .25, did = -.5, didnt = -.5)))
pairs <- list(managed_minus_did = c("managed", "did"),
              didnt_fail_minus_did = c("didnt_fail", "did"),
              didnt_manage_minus_didnt = c("didnt_manage", "didnt"),
              failed_minus_didnt = c("failed", "didnt"))
for (id in names(pairs)) {
  pair <- pairs[[id]]
  add(id, "implicative_boost_by_pair", paste(pair, collapse = " - "),
      weight(setNames(c(1, -1), pair)))
}
add("managed_and_didnt_fail_minus_did", "implicative_boost_grouped",
    "mean(managed, didnt_fail) - did", weight(c(managed = .5, didnt_fail = .5, did = -1)))
add("didnt_manage_and_failed_minus_didnt", "implicative_boost_grouped",
    "mean(didnt_manage, failed) - didnt",
    weight(c(didnt_manage = .5, failed = .5, didnt = -1)))
add("positive_outcome_grouped", "positive_outcome_contrasts",
    "mean(managed, didnt_fail) - mean(didnt_manage, failed)",
    weight(c(managed = .5, didnt_fail = .5, didnt_manage = -.5, failed = -.5)))
add("managed_minus_didnt_manage", "positive_outcome_contrasts",
    "managed - didnt_manage", weight(c(managed = 1, didnt_manage = -1)))
add("didnt_fail_minus_failed", "positive_outcome_contrasts",
    "didnt_fail - failed", weight(c(didnt_fail = 1, failed = -1)))
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
stopifnot(nobs(model) == nrow(d), ncol(x) == 11L, qr(x)$rank == 11L,
          nrow(contrasts) == 14L, !anyDuplicated(contrasts$analysis),
          all(is.finite(as.matrix(contrasts[c("estimate", "se", "df", "t", "p")]))),
          max(abs(contrasts$estimate - drop(L %*% lme4::fixef(model)))) < 1e-12,
          max(abs(contrasts$se - sqrt(diag(L %*% as.matrix(vcov(model)) %*% t(L))))) < 1e-12,
          max(abs(contrasts$p - 2 * pt(abs(contrasts$t), contrasts$df, lower.tail = FALSE))) < 1e-12,
          identical(input_md5, unname(tools::md5sum(input_path))))
saveRDS(model, file.path(output_dir, "model.rds"))
write.csv(coefs, file.path(output_dir, "model_coefficients.csv"), row.names = FALSE)
write.csv(terms, file.path(output_dir, "model_term_tests.csv"), row.names = FALSE)
write.csv(contrasts, file.path(output_dir, "try_planned_contrasts.csv"), row.names = FALSE)
write.csv(vc, file.path(output_dir, "model_variance_components.csv"), row.names = FALSE)
write.csv(fit, file.path(output_dir, "model_fit_statistics.csv"), row.names = FALSE)
write.csv(data.frame(analysis = rownames(L), L, row.names = NULL, check.names = FALSE),
          file.path(output_dir, "contrast_weights.csv"), row.names = FALSE)
writeLines(c(paste("Input:", "results/results_main/main_combined_clean.csv"), paste("Input MD5:", input_md5),
             paste("UTC run time:", format(Sys.time(), tz = "UTC", usetz = TRUE)),
             capture.output(sessionInfo())), file.path(output_dir, "session_info.txt"))
writeLines(c("Additive TRY mixed-effects model with question order", model_formula,
             "Response: try_rating_01, scale 0-1. Estimation: REML.",
             "Reference levels: managed; low; TRY?; TRY-first (TRY?|P?|NAT). Item: package/photo.",
             "All p-values are unadjusted. Tests use Satterthwaite degrees of freedom.",
             "", capture.output(print(sm, correlation = FALSE)), "",
             capture.output(print(tt)), "", "Planned contrasts:",
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
report <- c("# TRY mixed-effects results with question order", "",
 paste("Model:", model_formula), "", paste("N =", nrow(d), "; response scale: 0-1."),
 "REML estimation using lmerTest/lme4. Item has package and photo levels.",
 "Prior, QUD and rating-order effects are common additive effects across all eight utterances.",
 "Rating order compares completion-first (P?|TRY?|NAT) with TRY-first (TRY?|P?|NAT).",
 "Naturalness is always last. The model contains main effects only.",
 "Coefficients and planned contrasts use two-sided Wald-type t-tests with Satterthwaite df.",
 "Overall terms use Type II F-tests with Satterthwaite denominator df. All p-values are unadjusted.",
 "Group contrasts average utterances equally. Their 95% CIs use the same t distribution.", "",
 "## Fit", "", paste("- Singular fit at tolerance 1e-4:", fit$singular),
 paste("- Fixed design rank:", fit$fixed_rank, "of", fit$fixed_columns),
 paste("- Optimizer code:", fit$optimizer_code),
 paste("- Convergence messages:", if (length(conv_messages)) paste(conv_messages, collapse = "; ") else "none"),
 sprintf("- Item variance: %.8f; SD: %.6f; ICC: %.6f.", item_var, sqrt(item_var), fit$icc),
 "- The two item levels provide limited information about the random-intercept variance.", "",
 "## Overall fixed effects", "", "| Term | NumDF | DenDF | F | p |",
 "|---|---:|---:|---:|---:|", term_rows, "",
 "## Planned contrasts", "", "| Analysis | Estimate | SE | df | t | p | 95% CI |",
 "|---|---:|---:|---:|---:|---:|---|", contrast_rows, "",
 "The contextual coefficients apply to all utterances under the additive model.",
 "Naturalness and completion are summarized descriptively in the main results directory.", "",
 "Reproduce with Rscript --vanilla results/try_question_order/analysis.R; requires lme4 and lmerTest.")
writeLines(report, file.path(output_dir, "RESULTS_SUMMARY.md"))
cat(paste(report, collapse = "\n"), "\n")


order_counts <- as.data.frame(table(qud = d$qud, rating_order = d$rating_order))
write.csv(order_counts, file.path(output_dir, "rating_order_counts.csv"), row.names = FALSE)
coefficient_order <- coefs[coefs$term == "rating_orderP?|TRY?|NAT", ]
contrast_order <- contrasts[contrasts$analysis == "rating_order_effect", ]
term_order <- terms[terms$term == "rating_order", ]
stopifnot(nrow(coefficient_order) == 1L, nrow(contrast_order) == 1L, nrow(term_order) == 1L,
          all(order_counts$Freq > 0),
          max(abs(as.numeric(coefficient_order[c("estimate", "se", "df", "t", "p")]) -
                  as.numeric(contrast_order[c("estimate", "se", "df", "t", "p")]))) < 1e-10,
          abs(term_order$F - contrast_order$t^2) < 1e-10,
          abs(term_order$p - contrast_order$p) < 1e-10)
saved <- readRDS(file.path(output_dir, "model.rds"))
stopifnot(inherits(saved, "lmerModLmerTest"),
          identical(formula(saved), formula(model)),
          nobs(saved) == nrow(d),
          identical(input_md5, unname(tools::md5sum(input_path))))
writeLines(c("PASS: input unchanged and all included participants retained.",
             "PASS: fixed design rank 11/11; 14 planned contrasts.",
             "PASS: contrast estimates, SEs and two-sided t p-values match matrix calculations.",
             "PASS: order coefficient, planned contrast and 1-df F test agree.",
             "PASS: saved model has the expected class, formula and sample size."),
           file.path(output_dir, "validation.txt"))
cat("\nQuestion-order analysis validation passed.\n")
