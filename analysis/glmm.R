#!/usr/bin/env Rscript
# ARS Mixed-Effects Model (GLMM)
#
# Mixed-effects logistic regression of `recommended ~ platform + category + (1|question_id)`
# on the brand-response-event level.
#
# This script RUNS ON REAL FILES ONLY. It does not fabricate data or results.
# Usage:
#   Rscript analysis/glmm.R --responses data/responses.jsonl \
#                            --annotations data/annotations.jsonl \
#                            --brand "HubSpot"
#
# Dependencies: lme4, jsonlite (install.packages(c("lme4","jsonlite")))

# ── Model specification ─────────────────────────────────────────────────────
#
# Outcome: `recommended` (binary) = 1 if class_code in {C4, C5}, else 0.
#   ADJUDICATE events are EXCLUDED from the model (per the "unknown is not zero"
#   rule and R-F.6; ADJUDICATE is not a negative recommendation).
#
# Fixed effects:
#   platform   — the AI platform that produced the response
#   category   — the MQC category (crm, pm, code)
#
# Random intercept:
#   (1 | question_id) — accounts for within-question correlation. Responses to
#   the same Market Question Cell are not independent (the question's stated
#   requirements shape which brands get recommended). The random intercept
#   absorbs this correlation. Omitting it would underestimate standard errors
#   and inflate Type I error.
#
# ── Cluster-robust alternative ──────────────────────────────────────────────
#
# If the random-intercept assumption (normally distributed question effects)
# is violated, a cluster-robust alternative is:
#   library(sandwich); library(lmtest)
#   m <- glm(recommended ~ platform + category, family = binomial, data = df)
#   coeftest(m, vcov = vcovCL, type = "HC1", cluster = ~question_id)
#
# This does not model the question-level variance but produces robust SEs for
# the fixed effects.
#
# ── Python/statsmodels equivalent ───────────────────────────────────────────
#
# For users who prefer Python:
#   import statsmodels.api as sm
#   import statsmodels.formula.api as smf
#   model = smf.mixedlm("recommended ~ platform + category",
#                       data=df, groups=df["question_id"],
#                       family=sm.families.Binomial())
#   result = model.fit()
#   print(result.summary())
#
# Note: statsmodels' Binomial mixed model support is less mature than lme4's.
# For production use, lme4 (R) is recommended.
#
# ── Descriptive association ≠ causation ─────────────────────────────────────
#
# This model estimates DESCRIPTIVE ASSOCIATION, not causation. The protocol
# (per the framework's Section 11 / observatory-marketplace separation) measures
# what AI platforms recommend; it does not claim that platforms CAUSE brand
# outcomes. Coefficients describe observed variation in recommendation rates
# across platforms and categories, holding question-level heterogeneity constant.
# They should not be interpreted as causal effects of platforms on brands.

suppressPackageStartupMessages({
  library(lme4)
  library(jsonlite)
})

# ── Argument parsing ────────────────────────────────────────────────────────

args <- commandArgs(trailingOnly = TRUE)
responses_path <- NULL
annotations_path <- NULL
brand_filter <- NULL

i <- 1
while (i <= length(args)) {
  if (args[i] == "--responses") {
    responses_path <- args[i + 1]; i <- i + 2
  } else if (args[i] == "--annotations") {
    annotations_path <- args[i + 1]; i <- i + 2
  } else if (args[i] == "--brand") {
    brand_filter <- args[i + 1]; i <- i + 2
  } else {
    i <- i + 1
  }
}

if (is.null(responses_path) || is.null(annotations_path)) {
  stop("Usage: Rscript glmm.R --responses <path> --annotations <path> [--brand <name>]")
}

# ── Load data ───────────────────────────────────────────────────────────────

responses <- stream_in(file(responses_path), verbose = FALSE)
annotations <- stream_in(file(annotations_path), verbose = FALSE)

# ── Build event-level analysis frame ────────────────────────────────────────

# Join annotations to responses on response_id
df <- merge(annotations, responses[, c("response_id", "question_id", "platform")],
            by = "response_id", suffixes = c(".ann", ".resp"))

# Use response platform if annotation platform differs
df$platform <- ifelse(is.na(df$platform.resp), df$platform.ann, df$platform.resp)

# Extract category from question_id (pattern: {category}-q{NN})
df$category <- sub("-q\\d+$", "", df$question_id.ann)

# Binary outcome: recommended = 1 if class_code in {C4, C5}
# ADJUDICATE excluded (unknown is not zero; R-F.6)
df <- df[df$class_code %in% c("C1","C2","C3","C4","C5","C6"), ]
df$recommended <- as.integer(df$class_code %in% c("C4", "C5"))

# Filter by brand if specified
if (!is.null(brand_filter)) {
  df <- df[df$brand == brand_filter, ]
  cat(sprintf("Filtered to brand: %s (%d events)\n", brand_filter, nrow(df)))
}

if (nrow(df) < 10) {
  stop("Insufficient data (< 10 events) for mixed-effects model.")
}

cat(sprintf("\nAnalysis frame: %d events, %d questions, %d platforms\n",
            nrow(df), length(unique(df$question_id.ann)), length(unique(df$platform))))

# ── Fit model ───────────────────────────────────────────────────────────────

# recommended ~ platform + category + (1 | question_id)
# question_id.ann is the MQC identifier from the annotation record
model <- glmer(
  recommended ~ platform + category + (1 | question_id.ann),
  data = df,
  family = binomial(link = "logit"),
  control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
)

cat("\n═══════════════════════════════════════════════════════════════\n")
cat("Mixed-Effects Logistic Regression\n")
cat("recommended ~ platform + category + (1 | question_id)\n")
cat("═══════════════════════════════════════════════════════════════\n\n")

print(summary(model))

cat("\n── Random effects (question-level variance) ──\n")
print(VarCorr(model))

cat("\n── Fixed effects (odds ratios with 95% CIs) ──\n")
fe <- fixef(model)
se <- sqrt(diag(vcov(model)))
or <- exp(fe)
or_lo <- exp(fe - 1.96 * se)
or_hi <- exp(fe + 1.96 * se)
or_table <- data.frame(
  term = names(fe),
  estimate = fe,
  std_error = se,
  odds_ratio = or,
  or_lower = or_lo,
  or_upper = or_hi,
  z_value = fe / se,
  p_value = 2 * pnorm(-abs(fe / se))
)
print(or_table, row.names = FALSE)

cat("\n── Note ──\n")
cat("Coefficients are DESCRIPTIVE ASSOCIATIONS, not causal effects.\n")
cat("ADJUDICATE events excluded (unknown is not zero; R-F.6).\n")
cat("Random intercept on question_id absorbs within-question correlation.\n")
