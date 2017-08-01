clc <- function() {
  cat("\014");
}

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
    if (c == "timestamp") 
      func <- function(x) { strptime(x, "%Y-%m-%d %H:%M:%S") }
    else
      func <- as.numeric;
    df[c] = lapply(df[c], func);
  }
  
  df
}
