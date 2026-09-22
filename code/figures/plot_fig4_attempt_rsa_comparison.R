#!/usr/bin/env Rscript

file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
if (length(file_arg) != 1L) stop("Run with Rscript.")
script_path <- normalizePath(sub("^--file=", "", file_arg), winslash = "/")
plot_dir <- dirname(script_path)
source(file.path(plot_dir, "condition_summary.R"))
project_dir <- dirname(dirname(plot_dir))
output_dir <- file.path(project_dir, "figures")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
input_path <- file.path(project_dir, "results", "results_main", "main_combined_clean.csv")
args <- commandArgs(trailingOnly = TRUE)
model_path <- if (length(args)) args[[1]] else
  file.path(project_dir, "RSA", "m2_backoff", "outputs", "predictions.csv")
model_path <- normalizePath(model_path, winslash = "/", mustWork = TRUE)

required <- c("readr", "dplyr", "ggplot2", "gtable")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing R packages: ", paste(missing, collapse = ", "))
suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
})

utterance_order <- c(
  "didnt_try", "didnt", "failed", "didnt_manage",
  "did", "didnt_fail", "managed", "tried"
)
utterance_labels <- c(
  failed = "failed", didnt_manage = "didn't manage", didnt = "didn't",
  didnt_try = "didn't try", tried = "tried", did = "did",
  didnt_fail = "didn't fail", managed = "managed"
)

observed <- read_csv(input_path, show_col_types = FALSE) %>%
  filter(analysis_status == "include", utterance_id %in% utterance_order) %>%
  mutate(rating = as.numeric(try_rating) / 100) %>%
  filter(!is.na(rating)) %>%
  equal_condition_summary("utterance_id")

stopifnot(nrow(observed) == 8L, !anyNA(observed),
          !anyDuplicated(observed$utterance_id), all(observed$n > 1L),
          all(observed$cells == 8L),
          all(observed$lower <= observed$mean), all(observed$upper >= observed$mean))
model <- read_csv(model_path, show_col_types = FALSE)
stopifnot(nrow(model) == 8L, !anyDuplicated(model$utterance_id),
          setequal(model$utterance_id, utterance_order),
          max(abs(model$overall_l1 - (model$high_l1 + model$low_l1) / 2)) < 1e-12,
          max(abs(model$overall_backoff - (model$high_backoff + model$low_backoff) / 2)) < 1e-12)

comparison <- observed %>%
  left_join(model %>% select(utterance_id, overall_l1, overall_backoff), by = "utterance_id") %>%
  mutate(x = match(utterance_id, utterance_order) / 2) %>%
  arrange(x)
stopifnot(!anyNA(comparison), all(comparison$overall_l1 >= 0 & comparison$overall_l1 <= 1),
          all(comparison$overall_backoff >= 0 & comparison$overall_backoff <= 1))

series_order <- c("Human", "M-causal", "M-backoff")
series_colours <- c(
  "Human" = "black",
  "M-causal" = "#A8DDB5",  # Darker green from the original violin.
  "M-backoff" = "#F6C28B" # Darker yellow from the original violin.
)
points <- bind_rows(
  comparison %>% transmute(utterance_id, x, value = mean, series = "Human"),
  comparison %>% transmute(utterance_id, x = x, value = overall_l1, series = "M-causal"),
  comparison %>% transmute(utterance_id, x = x, value = overall_backoff, series = "M-backoff")
) %>% mutate(series = factor(series, levels = series_order))

plot <- ggplot() +
  geom_errorbar(
    data = comparison,
    aes(x = x, ymin = lower, ymax = upper),
    width = 0.0470021177, linewidth = 0.7, colour = "black"
  ) +
  geom_point(
    data = filter(points, series == "Human"),
    aes(x = x, y = value, colour = series), shape = 16, size = 4
  ) +
  geom_point(
    data = filter(points, series != "Human"),
    aes(x = x, y = value, colour = series), shape = 16, size = 4
  ) +
  scale_colour_manual(values = series_colours, breaks = series_order) +
  scale_x_continuous(
    breaks = seq_along(utterance_order) / 2,
    labels = unname(utterance_labels[utterance_order]),
    limits = c(0.25, 4.25), expand = expansion(mult = 0)
  ) +
  scale_y_continuous(
    limits = c(0, 1), breaks = seq(0, 1, 0.2),
    labels = function(x) ifelse(x == 1, "1", ifelse(x == 0, "0", sub("^0\\.", ".", sprintf("%.1f", x)))),
    minor_breaks = seq(0, 1, 0.1),
    expand = expansion(mult = c(0.025, 0.025))
  ) +
  labs(x = "utterance", y = "Inference probability", colour = NULL) +
  theme_bw(base_size = 15, base_family = "sans") +
  theme(
    panel.border = element_blank(),
    panel.grid.major.x = element_line(colour = "#E5E5E5", linewidth = 0.4),
    panel.grid.minor.x = element_blank(),
    panel.grid.major.y = element_line(colour = "#E5E5E5", linewidth = 0.4),
    panel.grid.minor.y = element_line(colour = "#EFEFEF", linewidth = 0.3),
    axis.text = element_text(size = 12, colour = "#333333"),
    axis.text.x = element_text(margin = margin(t = 5)),
    axis.title.x = element_text(size = 15, margin = margin(t = 9)),
    axis.title.y = element_text(size = 15, margin = margin(r = 8)),
    legend.position = "top", legend.justification = "center",
    legend.text = element_text(size = 12),
    legend.key.width = grid::unit(18, "pt"),
    legend.margin = margin(0, 0, 2.5, 0),
    legend.box.spacing = grid::unit(7.5, "pt"),
    plot.margin = margin(8, 12, 8, 8)
  ) +
  guides(colour = guide_legend(nrow = 1, override.aes = list(size = 4)))

grDevices::pdf(file = NULL, width = 8.28242902, height = 4.6)
plot_grob <- ggplotGrob(plot)
panel <- plot_grob$layout[plot_grob$layout$name == "panel", ]
stopifnot(nrow(panel) == 1L)
frame_gp <- grid::gpar(col = "#4A4A4A", fill = NA, lty = "solid",
                       lwd = 0.55 * 72.27 / 25.4)
plot_grob <- gtable::gtable_add_grob(
  plot_grob, grid::rectGrob(gp = frame_gp),
  t = panel$t, b = panel$b, l = panel$l, r = panel$r,
  z = Inf, clip = "off", name = "full-panel-frame"
)

invisible(grDevices::dev.off())

stem <- "fig4_attempt_rsa_comparison"
ggsave(
  file.path(output_dir, paste0(stem, ".pdf")), plot = plot_grob,
  device = cairo_pdf, fallback_resolution = 600,
  width = 8.28242902, height = 4.6, units = "in", bg = "white"
)
message("Wrote comparison figure to: ", output_dir)
