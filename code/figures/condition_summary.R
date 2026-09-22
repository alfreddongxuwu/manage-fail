condition_keys <- c("item", "prior", "qud", "utterance_id")

equal_condition_summary <- function(data, groups, rating = "rating") {
  stopifnot(all(c(condition_keys, groups, rating) %in% names(data)),
            all(is.finite(data[[rating]])))
  cells <- data %>%
    ungroup() %>%
    group_by(across(all_of(unique(c(groups, condition_keys))))) %>%
    summarise(
      cell_n = n(),
      cell_mean = mean(.data[[rating]]),
      cell_var = var(.data[[rating]]),
      .groups = "drop"
    )
  stopifnot(all(cells$cell_n > 1L), !anyNA(cells$cell_var))
  cells %>%
    group_by(across(all_of(groups))) %>%
    summarise(
      n = sum(cell_n), cells = n(), mean = mean(cell_mean),
      sd = sqrt(mean(cell_var + (cell_mean - mean(cell_mean))^2)),
      variance_sum = sum(cell_var / cell_n),
      df_denominator = sum((cell_var / cell_n)^2 / (cell_n - 1)),
      se = sqrt(variance_sum) / cells,
      df = if_else(df_denominator > 0,
                   variance_sum^2 / df_denominator, Inf),
      critical_t = qt(0.975, df = df),
      lower = pmax(0, mean - critical_t * se),
      upper = pmin(1, mean + critical_t * se),
      .groups = "drop"
    ) %>%
    select(-variance_sum, -df_denominator)
}

equal_condition_weights <- function(data, within = "utterance_id") {
  data %>%
    ungroup() %>%
    group_by(across(all_of(condition_keys))) %>%
    mutate(cell_weight = 1 / n()) %>%
    group_by(across(all_of(within))) %>%
    mutate(cell_weight = cell_weight / sum(cell_weight)) %>%
    ungroup()
}
