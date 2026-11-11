# =============================================================================
# tools/download_finn15_years.R  (11 Nov 2026; copy of download_finn15_missing_years.R, version 3)
# -----------------------------------------------------------------------------
# Gets and checks the FINN v1.5 GEOS-Chem annual files that were missing or
# invalid in after_08112026read/data (2002 had no file; the 2016 and 2017 files
# were copies of 2015) and the 2015 file, used to check the conversion of the raw
# files against the authors' converted 2015 file.
#
# File names on the NCAR server: FINNv1.5_<year>.GEOSCHEM.tar.gz for every year,
# 2002 included (the ".txt.gz" address of 2002 used by the earlier scripts returns
# 404; correct address confirmed by the authors on 11 Nov 2026). The FINN page
# (https://www.acom.ucar.edu/Data/fire/) asks users to submit their name and
# contact information before downloading these files: do that first.
#
# For each year the script:
#   1. uses a file already saved in out_dir, whatever its name, if the name has
#      the year and "FINN" or "GEOS" (e.g. a file downloaded through the form);
#   2. otherwise tries the server with the known file names (.tar.gz, .txt.gz,
#      .zip, .txt) and downloads the first one that exists;
#   3. identifies the format by the file content (gzip, tar, zip or text), checks
#      that compressed files are complete and extracts the emissions table into
#      FINNv1.5_<year>/ (the downloaded file is kept as it is);
#   4. records the MD5 of the file and of the table, the number of rows, the DAY
#      range and the header, and flags years whose tables are identical.
# Output: <out_dir>/finn15_download_check.csv
#
# Use in R or RStudio:  source("download_finn15_missing_years.R")
# or in a terminal:     Rscript download_finn15_missing_years.R [out_dir] [base_url]
# Only base R is required; data.table, if installed, is used to read DAY.
# Model reference: Wiedinmyer et al. (2011), https://doi.org/10.5194/gmd-4-625-2011
# =============================================================================

out_dir  <- "data/raw_finn/finn15_annual"   # folder for the downloaded files (ignored by git); change if needed
years    <- c(2002, 2015, 2016, 2017)
base_url <- "https://www.acom.ucar.edu/Data/fire/data/finn1"
form_url <- "https://www.acom.ucar.edu/Data/fire/"

args <- commandArgs(trailingOnly = TRUE)
if (length(args) >= 1) out_dir  <- args[1]
if (length(args) >= 2) base_url <- args[2]

options(timeout = max(3600, getOption("timeout")))   # seconds per file
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

server_names <- function(year) {
  sprintf(c("FINNv1.5_%d.GEOSCHEM.tar.gz", "FINNv1.5_%d.GEOSCHEM.txt.gz",
            "FINNv1.5_%d.GEOSCHEM.zip", "FINNv1.5_%d.GEOSCHEM.txt"), year)
}

# HTTP status and Content-Length of the final response (redirects followed).
remote_info <- function(url) {
  h <- tryCatch(curlGetHeaders(url), error = function(e) NULL)
  if (is.null(h)) return(list(status = NA_integer_, size = NA_real_))
  cl <- grep("^content-length:", h, ignore.case = TRUE, value = TRUE)
  size <- if (length(cl)) as.numeric(trimws(sub("^[^:]*:", "", cl[length(cl)]))) else NA_real_
  list(status = as.integer(attr(h, "status")), size = size)
}

# Files in out_dir that look like the FINN v1.5 file of a year (any name).
local_files <- function(year) {
  f <- list.files(out_dir, full.names = TRUE)
  f <- f[!dir.exists(f) & !grepl("\\.part$", f) & basename(f) != "finn15_download_check.csv"]
  b <- basename(f)
  f[grepl(paste0("(^|[^0-9])", year, "([^0-9]|$)"), b) & grepl("finn|geos", b, ignore.case = TRUE)]
}

# Format from the content: "gzip+tar", "gzip", "zip", "tar", "html" or "text".
file_kind <- function(path) {
  con <- file(path, "rb"); b <- readBin(con, "raw", n = 300); close(con)
  if (length(b) >= 2 && b[1] == as.raw(0x1f) && b[2] == as.raw(0x8b)) {
    g <- gzfile(path, "rb"); d <- readBin(g, "raw", n = 300); close(g)
    return(if (length(d) >= 262 && rawToChar(d[258:262]) == "ustar") "gzip+tar" else "gzip")
  }
  if (length(b) >= 4 && all(b[1:4] == as.raw(c(0x50, 0x4b, 0x03, 0x04)))) return("zip")
  if (length(b) >= 262 && rawToChar(b[258:262]) == "ustar") return("tar")
  txt <- tolower(rawToChar(b[b != as.raw(0)]))
  if (grepl("<html|<!doctype|<head|<title", txt)) return("html")
  "text"
}

# gzip check: bytes decompressed (mod 2^32) must equal ISIZE, the last 4 bytes.
# R reads a cut gzip file without any warning, so this check is needed.
gzip_ok <- function(path) {
  con <- file(path, "rb"); seek(con, file.size(path) - 4)
  isize <- readBin(con, "integer", size = 4, endian = "little"); close(con)
  if (isize < 0) isize <- isize + 2^32
  n <- 0; gz <- gzfile(path, "rb")
  ok <- tryCatch({
    repeat { b <- readBin(gz, "raw", n = 2^24); if (!length(b)) break; n <- n + length(b) }
    TRUE
  }, error = function(e) FALSE)
  close(gz)
  ok && (n %% 2^32) == isize
}

gunzip_to <- function(src, dst) {
  i <- gzfile(src, "rb"); o <- file(dst, "wb")
  repeat { b <- readBin(i, "raw", n = 2^24); if (!length(b)) break; writeBin(b, o) }
  close(i); close(o)
  dst
}

# Extracts the file and returns the emissions table: among the extracted files,
# the largest one whose first line has "DAY"; otherwise the largest one.
extract_table <- function(path, kind, exdir) {
  if (kind == "text") return(path)
  dir.create(exdir, showWarnings = FALSE)
  if (kind %in% c("gzip+tar", "tar")) utils::untar(path, exdir = exdir)
  if (kind == "zip") utils::unzip(path, exdir = exdir)
  if (kind == "gzip") {
    dst <- file.path(exdir, sub("\\.gz$", "", basename(path), ignore.case = TRUE))
    if (!grepl("\\.(txt|csv)$", dst, ignore.case = TRUE)) dst <- paste0(dst, ".txt")
    if (!file.exists(dst)) gunzip_to(path, dst)
  }
  f <- list.files(exdir, recursive = TRUE, full.names = TRUE)
  if (!length(f)) return(NA_character_)
  has_day <- vapply(f, function(x) {
    l <- tryCatch(readLines(x, n = 1, warn = FALSE), error = function(e) "")
    length(l) == 1 && grepl("DAY", l, ignore.case = TRUE)
  }, logical(1))
  pool <- if (any(has_day)) f[has_day] else f
  pool[which.max(file.size(pool))]
}

# Rows, DAY range (first column) and header line of an emissions table.
table_summary <- function(path) {
  hdr <- readLines(path, n = 1, warn = FALSE)
  s <- NULL
  if (requireNamespace("data.table", quietly = TRUE)) {
    s <- tryCatch({
      d <- data.table::fread(path, select = 1L, showProgress = FALSE)
      day <- suppressWarnings(as.numeric(d[[1]]))
      list(rows = nrow(d), day_min = min(day, na.rm = TRUE), day_max = max(day, na.rm = TRUE))
    }, error = function(e) NULL)
  }
  if (is.null(s)) {
    con <- file(path, "r"); n <- 0
    repeat { l <- readLines(con, n = 1e6, warn = FALSE); if (!length(l)) break; n <- n + length(l) }
    close(con)
    s <- list(rows = n - 1, day_min = NA, day_max = NA)
  }
  c(s, header = hdr)
}

log <- list()
for (year in years) {
  rec <- list(year = year, source = "", file = NA, bytes = NA, kind = NA, integrity = NA,
              md5_file = NA, table = NA, md5_table = NA, rows = NA, day_min = NA, day_max = NA,
              header = NA, identical_to = "")
  message("\n=== FINN v1.5 ", year)
  dest <- NA_character_

  loc <- local_files(year)
  if (length(loc)) {
    dest <- loc[which.max(file.size(loc))]
    rec$source <- "file already in out_dir"
    message("  using the file in out_dir: ", basename(dest))
  } else {
    for (nm in server_names(year)) {
      url <- paste0(base_url, "/", nm)
      ri <- remote_info(url)
      message("  server: ", nm, " -> HTTP ", ri$status,
              if (identical(ri$status, 200L) && !is.na(ri$size)) sprintf(", %.1f MB", ri$size / 2^20) else "")
      if (!identical(ri$status, 200L) || (!is.na(ri$size) && ri$size < 10240)) next
      d <- file.path(out_dir, nm); part <- paste0(d, ".part")
      st <- tryCatch(download.file(url, part, mode = "wb", method = "libcurl", quiet = FALSE),
                     error = function(e) { message("  FAILED: ", conditionMessage(e)); NA })
      if (isTRUE(st == 0) && file.exists(part) && (is.na(ri$size) || file.size(part) == ri$size)) {
        file.rename(part, d); dest <- d; rec$source <- url
      } else {
        rec$source <- paste("incomplete download (kept as .part):", url)
        message("  incomplete download; kept as ", basename(part), "; run the script again")
      }
      break
    }
    if (is.na(dest) && !nzchar(rec$source)) {
      rec$source <- "not found on the server under the known names"
      message("  not found on the server. Get it through the form at ", form_url,
              " (FINNv1.5, ", year, ", GEOS-Chem), save it in ", out_dir, " and run this script again.")
    }
  }

  if (!is.na(dest) && file.exists(dest)) {
    rec$file <- basename(dest); rec$bytes <- file.size(dest)
    rec$md5_file <- unname(tools::md5sum(dest))
    rec$kind <- file_kind(dest)
    rec$integrity <- switch(rec$kind,
      "gzip" = , "gzip+tar" = if (gzip_ok(dest)) "gzip OK" else "gzip FAILED (cut or damaged)",
      "zip"  = if (!is.null(tryCatch(utils::unzip(dest, list = TRUE), error = function(e) NULL))) "zip OK" else "zip FAILED",
      "html" = "HTML page, not a data file (delete it and get the file again)",
      "not compressed")
    message("  format: ", rec$kind, "; ", rec$integrity)
    if (!grepl("FAILED|HTML", rec$integrity)) {
      tab <- tryCatch(extract_table(dest, rec$kind, file.path(out_dir, sprintf("FINNv1.5_%d", year))),
                      error = function(e) { message("  extraction failed: ", conditionMessage(e)); NA })
      if (!is.na(tab)) {
        s <- table_summary(tab)
        rec$table <- tab; rec$md5_table <- unname(tools::md5sum(tab))
        rec$rows <- s$rows; rec$day_min <- s$day_min; rec$day_max <- s$day_max; rec$header <- s$header
        message(sprintf("  table: %s, %s rows, DAY %s to %s", basename(tab),
                        format(s$rows, big.mark = ","), s$day_min, s$day_max))
      }
    }
  }
  log[[length(log) + 1]] <- rec
}

res <- do.call(rbind, lapply(log, function(r) as.data.frame(r, stringsAsFactors = FALSE)))
for (i in seq_len(nrow(res))) {
  if (is.na(res$md5_table[i])) next
  same <- res$year[!is.na(res$md5_table) & res$md5_table == res$md5_table[i] & seq_len(nrow(res)) != i]
  if (length(same)) res$identical_to[i] <- paste(same, collapse = ";")
}
out_csv <- file.path(out_dir, "finn15_download_check.csv")
utils::write.csv(res, out_csv, row.names = FALSE)

message("\n=== Summary")
print(res[, c("year", "file", "kind", "integrity", "rows", "day_min", "day_max", "identical_to")], row.names = FALSE)
if (any(nzchar(res$identical_to))) {
  message("WARNING: some years have identical tables; they are not data of different years.")
}
message("Check table written to: ", out_csv)
