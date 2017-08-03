library(lubridate);
library(xts);

# handy console function..
clc <- function() {
  cat("\014");
}

# load timeseries data
# path := path containing list of csv files
# pattern := load the files that follow `pattern`
load_df <- function(path, pattern) {
  # load all files
  files <- dir(path=path, pattern=pattern, full.name=TRUE);
  df <- do.call(rbind, lapply(files, read.csv));
  
  # update column names
  cols <- colnames(df);
  cols[1] <- "timestamp";
  colnames(df) <- cols;
  
  # null values
  df[df == "\\N"] <- NA;
  
  # update data types
  for (c in colnames(df)) {
    if (c == "timestamp") {
      df[c] <- lapply(df[c], ymd_hms);
    } else {
      df[c] <- lapply(df[c], as.numeric);
    }
  }
  
  # conver to timeseries.
  df <- xts(df, order.by=df$timestamp);
  
  df
}
