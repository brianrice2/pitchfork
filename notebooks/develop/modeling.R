library(tidyverse)
library(ALEPlot)   # ALE plots
library(nnet)      # neural networks
library(rpart)     # CARTs
library(yaImpute)  # K-NN
library(mgcv)      # GAM
library(gbm)       # gradient boosted trees
library(randomForest)

df <- read_csv("../../data/cleaned/P4KxSpotify.csv")
df$genre <- as.factor(df$genre)

# Generate partitions (by index) for cross-validation
#' n is sample size
#' K is number of folds
#' returns K-length list of indices for each folds
CVInd <- function(n, K) {
  m <- floor(n / K) # approximate size of each folds
  r <- n - m * K
  I <- sample(n, n) # random reordering of the indices
  Ind <- list()     # store list of indices for all K folds
  length(Ind) <- K
  for (k in 1:K) {
    if (k <= r) {
      kth_fold <- ((m + 1) * (k - 1) + 1):((m + 1) * k)
    } else {
      kth_fold <- ((m + 1) * r + m * (k - r - 1) + 1):((m + 1) * r + m * (k - r))
    }
    Ind[[k]] <- I[kth_fold] # indices for kth fold of data
  }
  Ind
}


# CV for just neural network architecture -------------------------------------------

n_replicates <- 3
K <- 5
n <- nrow(df)
y <- df$score

lambda <- 10 ** c(-2, -1, 0, 1)
size <- c(1, 3, 5, 10)
param_combos <- crossing(lambda, size)
n_models <- nrow(param_combos)

y_hat <- matrix(0, n, n_models)
MSE <- matrix(0, n_replicates, n_models)

set.seed(12345)
for (j in 1:n_replicates) {
  print(c("Starting replicate ", j))
  Ind <- CVInd(n, K)

  for (k in 1:K) {
    print(c("Starting k = ", k))
    for (model_idx in 1:n_models) {
      combo <- param_combos[model_idx, ]
      nnet_fit <- nnet(score ~ releaseyear + genre + danceability + energy +
                         key + loudness + speechiness + acousticness +
                         instrumentalness + liveness + valence + tempo,
                       data = df[-Ind[[k]], ], maxit = 1000, trace = FALSE,
                       size = combo$size, decay = combo$lambda)
      y_hat[Ind[[k]], model_idx] <- as.numeric(predict(nnet_fit, df[Ind[[k]], ], type = "raw"))
    }
  }
  # MSE_CV = SSE_CV / n
  MSE[j, ] <- apply(y_hat, 2, function(x) sum((y - x)**2)) / n
}

MSEAve <- apply(MSE, 2, mean)
RMSEAve <- sqrt(MSEAve)
paste("RMSE:")
round(RMSEAve, 4)

best_model_row <- which.min(MSEAve)
best_params <- param_combos[best_model_row, ]
best_lambda <- best_params$lambda
best_size <- best_params$size
paste(best_lambda, best_size)


# CV across models ------------------------------------------------------------------

n_replicates <- 3
K <- 5
n <- nrow(df)
y <- df$score
n_models <- 3
y_hat <- matrix(0, n, n_models)
MSE <- matrix(0, n_replicates, n_models)

set.seed(12345)
for (j in 1:n_replicates) {
  print(c("Starting replicate ", j))
  Ind <- CVInd(n, K)

  for (k in 1:K) {
    print(c("Starting k = ", k))
    # Linear model
    model_number <- 1
    linear_fit <- lm(score ~ releaseyear + genre + danceability + energy +
                       key + loudness + speechiness + acousticness +
                       instrumentalness + liveness + valence + tempo,
                     data = df[-Ind[[k]], ])
    y_hat[Ind[[k]], model_number] <- as.numeric(predict(linear_fit, df[Ind[[k]], ]))

    # GAM
    model_number <- model_number + 1
    gam_fit <- gam(score ~ s(releaseyear) + genre + s(danceability) + s(energy) +
                     s(key) + s(loudness) + s(speechiness) + s(acousticness) +
                     s(instrumentalness) + s(liveness) + s(valence) + s(tempo),
                   data = df[-Ind[[k]], ], family = gaussian())
    y_hat[Ind[[k]], model_number] <- as.numeric(predict(gam_fit, df[Ind[[k]], ]))

    # Simple neural network
    model_number <- model_number + 1
    nnet_fit <- nnet(score ~ releaseyear + genre + danceability + energy +
                       key + loudness + speechiness + acousticness +
                       instrumentalness + liveness + valence + tempo,
                     data = df[-Ind[[k]], ], maxit = 1000, trace = FALSE,
                     size = 15, decay = 0.01)
    y_hat[Ind[[k]], model_number] <- as.numeric(predict(nnet_fit, df[Ind[[k]], ]))
  }
  # MSE_CV = SSE_CV / n
  MSE[j, ] <- apply(y_hat, 2, function(x) sum((y - x)**2)) / n
}

MSEAve <- apply(MSE, 2, mean)
RMSEAve <- sqrt(MSEAve)
paste("RMSE:")
round(RMSEAve, 4)


# Linear model on full dataset ------------------------------------------------------
# (to check residuals)

linear_fit <- lm(score ~ releaseyear + genre + danceability + energy +
                   key + loudness + speechiness + acousticness +
                   instrumentalness + liveness + valence + tempo,
                 data = df)
summary(linear_fit)
plot(linear_fit)



# Regression tree -------------------------------------------------------------------

# Trees do CV on their own, so run outside the main CV loop
control <- rpart.control(minbucket = 5, cp = 0.001, maxsurrogate = 0, usesurrogate = 0)
tree_fit <- rpart(score ~ releaseyear + genre + danceability + energy +
                    key + loudness + speechiness + acousticness +
                    instrumentalness + liveness + valence + tempo,
                  data = df, method = "anova", control = control)
plotcp(tree_fit)

# prune back to optimal size, according to plot of CV 1 - R-squared
# left-most value below the horizontal line is about cp = 0.01
tree_fit <- prune(tree_fit, cp = 0.01)

preds <- predict(tree_fit, df)
SSE <- sum((df$score - preds)**2)
MSE <- SSE / n
RMSE <- sqrt(MSE)
paste("RMSE:")
round(RMSE, 4)


# Gradient-boosted tree -------------------------------------------------------------

set.seed(3947)
gbm_fit <- gbm(score ~ releaseyear + genre + danceability + energy +
                 key + loudness + speechiness + acousticness +
                 instrumentalness + liveness + valence + tempo,
               data = df, var.monotone = rep(0, 12),
               distribution = "gaussian", n.trees = 5000, shrinkage = 0.005,
               interaction.depth = 3, bag.fraction = 0.5, train.fraction = 1,
               n.minobsinnode = 5, cv.folds = 10, keep.data = TRUE, verbose = FALSE)
best.iter <- gbm.perf(gbm_fit, method = "cv")
preds <- predict(gbm_fit, data, n.trees = best.iter)
SSE <- sum((df$score - preds)**2)
MSE <- SSE / n
RMSE <- sqrt(MSE)
paste("RMSE:")
round(RMSE, 4)
