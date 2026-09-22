#!/usr/bin/env Rscript


args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
if (length(file_arg) == 0) {
  stop("Run this script with Rscript so the project path can be resolved.")
}

script_path <- normalizePath(
  sub("^--file=", "", file_arg[1]),
  winslash = "/",
  mustWork = TRUE
)
plot_dir <- dirname(script_path)
source(file.path(plot_dir, "condition_summary.R"))
project_dir <- dirname(dirname(plot_dir))
input_path <- file.path(project_dir, "results", "results_main", "main_combined_clean.csv")
output_dir <- file.path(project_dir, "figures")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

required <- c("readr", "dplyr", "ggplot2", "gtable")
missing <- required[
  !vapply(required, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing) > 0) {
  stop("Missing required R package(s): ", paste(missing, collapse = ", "))
}

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
})

utterance_order <- c(
  "managed",
  "didnt_manage",
  "failed",
  "didnt_fail",
  "did",
  "didnt",
  "tried",
  "didnt_try"
)

utterance_labels <- c(
  managed = "managed",
  didnt_manage = "didn't manage",
  failed = "failed",
  didnt_fail = "didn't fail",
  did = "did",
  didnt = "didn't",
  tried = "tried",
  didnt_try = "didn't try"
)

family_labels <- c("managed", "failed", "did", "tried")
polarity_labels <- setNames(rep(c("pos", "neg"), 4), utterance_order)

d <- read_csv(input_path, show_col_types = FALSE) %>%
  filter(
    analysis_status == "include",
    utterance_id %in% utterance_order
  )

ratings_raw <- d %>%
  transmute(
    utterance_id, item, prior, qud,
    rating_type = "Attempt",
    rating = as.numeric(try_rating) / 100
  ) %>%
  filter(!is.na(rating)) %>%
  equal_condition_weights() %>%
  mutate(
    utterance_id = factor(utterance_id, levels = utterance_order),
    rating_type = factor(rating_type, levels = "Attempt"),
    fill_group = factor(unname(polarity_labels[as.character(utterance_id)]),
                        levels = c("pos", "neg"))
  )

ratings_summary <- equal_condition_summary(
  ratings_raw, c("utterance_id", "rating_type")
)
stopifnot(nrow(ratings_summary) == 8L, all(ratings_summary$cells == 8L))

plot <- ggplot(
  ratings_raw,
  aes(x = rating_type, y = rating, fill = fill_group)
) +
  geom_violin(
    aes(colour = fill_group, weight = cell_weight),
    trim = TRUE,
    quantiles = NULL,
    scale = "width",
    adjust = 1.05,
    width = 0.62,
    linewidth = 0.55
  ) +
  geom_errorbar(
    data = ratings_summary,
    aes(x = rating_type, ymin = lower, ymax = upper),
    inherit.aes = FALSE,
    width = 0.12,
    linewidth = 0.7,
    colour = "black"
  ) +
  geom_point(
    data = ratings_summary,
    aes(x = rating_type, y = mean),
    inherit.aes = FALSE,
    shape = 21,
    size = 3,
    stroke = 0.55,
    fill = "black",
    colour = "black"
  ) +
  facet_wrap(
    vars(utterance_id),
    ncol = 8,
    labeller = as_labeller(polarity_labels)
  ) +
  scale_fill_manual(
    values = scales::alpha(c(
      "pos" = "#D3D3D3",
      "neg" = "#A9A9A9"
    ), 1)
  ) +
  scale_colour_manual(values = c("pos" = "#D3D3D3", "neg" = "#A9A9A9")) +
scale_y_continuous(
    limits = c(0, 1),
    breaks = seq(0, 1, 0.2),
    labels = function(x) ifelse(x == 1, "1", ifelse(x == 0, "0", sub("^0\\.", ".", sprintf("%.1f", x)))),
    minor_breaks = seq(0, 1, 0.1),
    expand = expansion(mult = c(0.025, 0.025))
  ) +
  labs(
    x = "Attempt inference",
    y = "Mean inference rating",
    fill = NULL
  ) +
  theme_bw(base_size = 15, base_family = "sans") +
  theme(
    panel.grid.major.x = element_line(colour = "#E5E5E5", linewidth = 0.4),
    panel.grid.minor.x = element_blank(),
    panel.grid.minor.y = element_line(colour = "#EFEFEF", linewidth = 0.3),
    panel.grid.major.y = element_line(colour = "#E5E5E5", linewidth = 0.4),
    panel.border = element_blank(),
    strip.background = element_rect(
      fill = "#E2E2E2",
      colour = NA,
      linewidth = 0.55
    ),
    strip.text = element_text(
      size = 12,
      colour = "black",
      face = "plain",
      margin = margin(4, 3, 4, 3)
    ),
    axis.text = element_text(size = 12, colour = "#333333"),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    axis.title.x = element_text(size = 15, margin = margin(t = 7)),
    axis.title.y = element_text(size = 15, margin = margin(r = 8)),
    legend.position = "none",
    panel.spacing = unit(0, "pt"),
    plot.margin = margin(8, 10, 8, 8)
  )

grDevices::pdf(file = NULL, width = 9.4, height = 3.7)
plot_grob <- ggplotGrob(plot)
strips <- plot_grob$layout[grepl("^strip-t-", plot_grob$layout$name), ]
strips <- strips[order(strips$l), ]
stopifnot(nrow(strips) == 8L, length(unique(strips$t)) == 1L)
for (i in c(2L, 4L, 6L)) {
  gap_columns <- seq.int(strips$r[i] + 1L, strips$l[i + 1L] - 1L)
  plot_grob$widths[gap_columns] <- grid::unit(0, "pt")
  plot_grob$widths[gap_columns[ceiling(length(gap_columns) / 2)]] <- grid::unit(12, "pt")
}
header_row <- min(strips$t)
plot_grob <- gtable::gtable_add_rows(plot_grob, grid::unit(21, "pt"), pos = header_row - 1L)
for (i in seq_along(family_labels)) {
  header <- grid::grobTree(
    grid::rectGrob(gp = grid::gpar(fill = "#E2E2E2", col = NA,
                                 lwd = 0.55 * 72.27 / 25.4)),
    grid::textGrob(family_labels[i], gp = grid::gpar(fontfamily = "sans",
                                                   fontsize = 12, col = "black"))
  )
  plot_grob <- gtable::gtable_add_grob(
    plot_grob, header, t = header_row, b = header_row,
    l = strips$l[2L * i - 1L], r = strips$r[2L * i],
    clip = "off", name = paste0("family-header-", i)
  )
}
panels <- plot_grob$layout[grepl("^panel-", plot_grob$layout$name), ]
panels <- panels[order(panels$l), ]
stopifnot(nrow(panels) == 8L, length(unique(panels$t)) == 1L)
frame_gp <- grid::gpar(col = "#4A4A4A", fill = NA,
                       lwd = 0.55 * 72.27 / 25.4)
family_header_depth <- plot_grob$heights[header_row]
all_header_depth <- sum(plot_grob$heights[header_row:(panels$t[1] - 1L)])
family_rule_y <- grid::unit(1, "npc") - family_header_depth
panel_rule_y <- grid::unit(1, "npc") - all_header_depth
for (i in seq_along(family_labels)) {
  frame <- grid::grobTree(
    grid::rectGrob(gp = frame_gp),
    grid::segmentsGrob(x0 = 0, x1 = 1, y0 = family_rule_y,
                       y1 = family_rule_y, gp = frame_gp),
    grid::segmentsGrob(x0 = 0, x1 = 1, y0 = panel_rule_y,
                       y1 = panel_rule_y, gp = frame_gp),
    grid::segmentsGrob(x0 = 0.5, x1 = 0.5, y0 = 0,
                       y1 = family_rule_y, gp = frame_gp)
  )
  plot_grob <- gtable::gtable_add_grob(
    plot_grob, frame, t = header_row, b = panels$b[2L * i],
    l = panels$l[2L * i - 1L], r = panels$r[2L * i],
    clip = "off", name = paste0("family-frame-", i)
  )
}
invisible(grDevices::dev.off())

ggsave(
  filename = file.path(output_dir, "fig2_try_inference.pdf"),
  plot = plot_grob,
  device = cairo_pdf,
  fallback_resolution = 600,
  width = 9.4,
  height = 3.7,
  units = "in"
)



message("Wrote figure files to: ", output_dir)
