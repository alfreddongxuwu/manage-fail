#!/usr/bin/env Rscript


file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
if (length(file_arg) != 1L) stop("Run this script with Rscript.")
script_path <- normalizePath(sub("^--file=", "", file_arg), winslash = "/", mustWork = TRUE)
project_dir <- dirname(dirname(dirname(script_path)))
source(file.path(dirname(script_path), "condition_summary.R"))
input_path <- file.path(project_dir, "results", "results_main", "main_combined_clean.csv")
output_dir <- file.path(project_dir, "figures")
required <- c("readr", "dplyr", "ggplot2", "patchwork", "gtable")
missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) stop("Missing R packages: ", paste(missing, collapse = ", "))
suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(patchwork)
})

implicatives <- c("managed", "failed", "didnt_manage", "didnt_fail")
positive_polarity <- c("managed", "failed")
positive_outcome <- c("managed", "didnt_fail")
negative_outcome <- c("didnt_manage", "failed")
baselines <- c("did", "didnt")

d <- read_csv(input_path, show_col_types = FALSE) %>%
  filter(analysis_status == "include", utterance_id %in% c(implicatives, baselines)) %>%
  mutate(attempt_rating = as.numeric(try_rating) / 100) %>%
  filter(!is.na(attempt_rating))
stopifnot(all(is.finite(d$attempt_rating)),
          all(d$attempt_rating >= 0 & d$attempt_rating <= 1))

summarise_ci <- function(data) {
  equal_condition_summary(data, group_vars(data), "attempt_rating")
}

imp_data <- d %>% filter(utterance_id %in% implicatives) %>%
  mutate(polarity = factor(if_else(utterance_id %in% positive_polarity, "positive", "negative"),
                           levels = c("positive", "negative")))
prior_bars <- imp_data %>%
  mutate(condition = factor(prior, levels = c("high", "low"))) %>%
  group_by(condition, polarity) %>% summarise_ci()
prior_points <- imp_data %>%
  mutate(condition = factor(prior, levels = c("high", "low"))) %>%
  group_by(condition) %>% summarise_ci()
qud_bars <- imp_data %>%
  mutate(condition = factor(qud, levels = c("P?", "TRY?"))) %>%
  group_by(condition, polarity) %>% summarise_ci()
qud_points <- imp_data %>%
  mutate(condition = factor(qud, levels = c("P?", "TRY?"))) %>%
  group_by(condition) %>% summarise_ci()

boost_data <- d %>% mutate(
  condition = factor(if_else(utterance_id %in% c(positive_outcome, "did"),
                             "pos-outcome", "neg-outcome"),
                      levels = c("pos-outcome", "neg-outcome")),
  status = factor(if_else(utterance_id %in% baselines, "baseline", "implicative"),
                   levels = c("baseline", "implicative"))
)
boost_bars <- boost_data %>% group_by(condition, status) %>% summarise_ci()
boost_overall <- boost_data %>% group_by(status) %>% summarise_ci()

stopifnot(nrow(prior_bars) == 4L, nrow(qud_bars) == 4L,
          nrow(boost_bars) == 4L, nrow(prior_points) == 2L,
          nrow(qud_points) == 2L, sum(prior_bars$n) == nrow(imp_data),
          sum(qud_bars$n) == nrow(imp_data), sum(boost_bars$n) == nrow(d))
for (entry in list(list(prior_bars, prior_points), list(qud_bars, qud_points))) {
  for (j in seq_len(nrow(entry[[2]]))) {
    rows <- entry[[1]][entry[[1]]$condition == entry[[2]]$condition[j], ]
    stopifnot(abs(weighted.mean(rows$mean, rows$cells) - entry[[2]]$mean[j]) < 1e-12)
  }
}

fig3_theme <- function() {
  theme_bw(base_size = 15, base_family = "sans") +
    theme(
      panel.grid.major.x = element_line(colour = "#E5E5E5", linewidth = 0.4),
      panel.grid.major.y = element_line(colour = "#E5E5E5", linewidth = 0.4),
      panel.grid.minor.x = element_blank(),
      panel.grid.minor.y = element_line(colour = "#EFEFEF", linewidth = 0.3),
      panel.border = element_blank(),
      axis.text = element_text(size = 16, colour = "#333333"),
      axis.text.x = element_text(margin = margin(t = 4)),
      axis.title.x = element_text(size = 20, margin = margin(t = 7)),
      axis.title.y = element_text(size = 20, margin = margin(r = 8)),
      legend.position = "top", legend.title = element_blank(),
      legend.text = element_text(size = 16),
      legend.key.height = grid::unit(16, "pt"),
      plot.margin = margin(8, 10, 8, 8)
    )
}

fig3_y_scale <- function() {
  scale_y_continuous(
    limits = c(0, 1), breaks = seq(0, 1, 0.2),
    labels = function(x) ifelse(x == 1, "1", ifelse(x == 0, "0",
      sub("^0\\.", ".", sprintf("%.1f", x)))),
    minor_breaks = seq(0, 1, 0.1), expand = expansion(mult = c(0.025, 0.025))
  )
}

fig3_fill_values <- c(positive = "#D3D3D3", negative = "#A9A9A9",
                      baseline = "#F6C28B", implicative = "#A8DDB5")
fig3_fill_labels <- c("managed + failed", "didn't manage + didn't fail",
                      "Baseline", "Implicatives")
fig3_fill_scale <- function() {
  scale_fill_manual(values = fig3_fill_values, limits = names(fig3_fill_values),
                    breaks = names(fig3_fill_values), labels = fig3_fill_labels,
                    drop = FALSE, name = NULL, guide = guide_legend(order = 1, nrow = 1, byrow = TRUE, override.aes = list(alpha = c(1, 1, 1, 1))))
}

make_context_panel <- function(bars, points, x_title, x_labels) {
  bars <- bars %>% mutate(
    x = as.numeric(condition) + if_else(polarity == "positive", -0.18, 0.18)
  )
  points <- points %>% mutate(x = as.numeric(condition))
  ggplot() +
    geom_col(data = bars, aes(x = x, y = mean, fill = polarity),
             width = 0.36, colour = NA, show.legend = c(fill = TRUE, shape = FALSE)) +
    geom_errorbar(data = bars, aes(x = x, ymin = lower, ymax = upper),
                  width = 0.07, linewidth = 0.7, colour = "black") +
    geom_errorbar(data = points, aes(x = x, ymin = lower, ymax = upper),
                  width = 0.05, linewidth = 0.7, colour = "black", show.legend = FALSE) +
    geom_point(data = points, aes(x = x, y = mean),
                colour = "black", shape = 16, size = 4, show.legend = FALSE) +
    fig3_fill_scale() +
    scale_x_continuous(breaks = 1:2, labels = x_labels,
                       limits = c(0.4, 2.6), expand = expansion(mult = 0)) +
    fig3_y_scale() + labs(x = x_title, y = "Mean inference rating") + fig3_theme()
}

prior_plot <- make_context_panel(prior_bars, prior_points, "Prior", c("high", "low"))
qud_plot <- make_context_panel(qud_bars, qud_points, "QUD", c("P?", "TRY?"))

boost_bar_positions <- boost_bars %>% mutate(
  x = as.numeric(condition) + if_else(status == "baseline", -0.18, 0.18)
)
boost_point_positions <- boost_overall %>% mutate(x = as.numeric(status))
for (j in seq_len(nrow(boost_overall))) {
  rows <- boost_bars[boost_bars$status == boost_overall$status[j], ]
  stopifnot(abs(weighted.mean(rows$mean, rows$cells) - boost_overall$mean[j]) < 1e-12)
}
boost_plot <- ggplot() +
  geom_col(data = boost_bar_positions, aes(x = x, y = mean, fill = status),
           width = 0.36, colour = NA, alpha = 1, show.legend = c(fill = TRUE, shape = FALSE)) +
  geom_errorbar(data = boost_bar_positions, aes(x = x, ymin = lower, ymax = upper),
                width = 0.07, linewidth = 0.7, colour = "black") +
  geom_errorbar(data = boost_point_positions, aes(x = x, ymin = lower, ymax = upper),
                width = 0.05, linewidth = 0.7, colour = "black", show.legend = FALSE) +
  geom_point(data = boost_point_positions, aes(x = x, y = mean),
               colour = "black", shape = 16, size = 4, show.legend = FALSE) +
  fig3_fill_scale() +
  scale_x_continuous(breaks = 1:2, labels = c("pos-outcome", "neg-outcome"),
                     limits = c(0.4, 2.6), expand = expansion(mult = 0)) +
  fig3_y_scale() + labs(x = "Implicative boost", y = "Mean inference rating") + fig3_theme()

plot <- (prior_plot | qud_plot | boost_plot) +
  patchwork::plot_layout(nrow = 1, widths = c(1, 1, 1), guides = "collect") &
  theme(legend.position = "top", legend.direction = "horizontal",
        legend.box = "horizontal", legend.justification = "center",
        legend.box.just = "center", legend.box.spacing = grid::unit(7.5, "pt"),
        legend.key.width = grid::unit(24, "pt"))

grDevices::pdf(file = NULL, width = 12.6, height = 5.6)
plot_grob <- patchwork::patchworkGrob(plot)
panel_cells <- plot_grob$layout[grepl("^panel-[0-9]+$", plot_grob$layout$name), ]
stopifnot(nrow(panel_cells) == 3L)
frame_gp <- grid::gpar(col = "#4A4A4A", fill = NA, lty = "solid",
                       lwd = 0.55 * 72.27 / 25.4)
for (i in seq_len(nrow(panel_cells))) {
  panel <- panel_cells[i, ]
  plot_grob <- gtable::gtable_add_grob(
    plot_grob, grid::rectGrob(gp = frame_gp),
    t = panel$t, b = panel$b, l = panel$l, r = panel$r,
    z = Inf, clip = "off", name = paste0("full-panel-frame-", i)
  )
}

invisible(grDevices::dev.off())

dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
ggsave(filename = file.path(output_dir, "fig3_effects.pdf"), plot = plot_grob,
       device = cairo_pdf, fallback_resolution = 600,
       width = 12.6, height = 5.6, units = "in", bg = "white")
message("Wrote Figure 3 PDF to: ", output_dir)
