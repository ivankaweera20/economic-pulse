import os
from typing import Any

import pandas as pd
import requests
import matplotlib.pyplot as plt


# Base URL used for every FRED API request
BASE_URL = "https://api.stlouisfed.org/fred"


# ============================================================
# API FUNCTIONS
# ============================================================

def fred_get(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    """
    Send a request to the FRED API and return the response as JSON.

    endpoint:
        The specific FRED API endpoint we want to use.

    params:
        The parameters we want to send to FRED,
        such as the series ID or starting date.
    """

    # Get the FRED API key from the environment variable
    api_key = os.getenv("FRED_API_KEY")

    # Stop the program if the API key cannot be found
    if not api_key:
        raise RuntimeError("FRED_API_KEY is not set.")

    # Add the API key and JSON format to whatever parameters were passed in
    request_params = {
        "api_key": api_key,
        "file_type": "json",
        **params,
    }

    # Send the request to FRED
    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        params=request_params,
        timeout=30,
    )

    # If FRED returns an error, try to display a useful error message
    if not response.ok:
        try:
            error = response.json().get("error_message", response.text)
        except ValueError:
            error = response.text

        raise RuntimeError(
            f"FRED request failed ({response.status_code}): {error}"
        )

    # Convert FRED's JSON response into a Python dictionary
    return response.json()


def get_series(
    series_id: str,
    observation_start: str = "2000-01-01",
    observation_end: str | None = None,
) -> pd.DataFrame:
    """
    Download one FRED economic series and return it as a pandas DataFrame.

    Example:
        get_series("UNRATE")

    would download the unemployment rate.
    """

    # Parameters sent to FRED
    params = {
        "series_id": series_id,
        "observation_start": observation_start,
        "sort_order": "asc",
    }

    # Only add an ending date if one was provided
    if observation_end:
        params["observation_end"] = observation_end

    # Ask FRED for observations from this series
    payload = fred_get("series/observations", params)

    # Get the list of observations from the JSON response
    observations = payload.get("observations", [])

    # If FRED returns no observations, return an empty DataFrame
    if not observations:
        return pd.DataFrame(
            columns=[series_id],
            index=pd.DatetimeIndex([], name="date"),
        )

    # Convert the observations into a pandas DataFrame
    frame = pd.DataFrame(observations)

    # Convert the date column from text into real dates
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")

    # Convert the value column from text into numbers
    frame[series_id] = pd.to_numeric(frame["value"], errors="coerce")

    # Keep only date and the economic series,
    # make date the index, and sort everything by date
    return (
        frame[["date", series_id]]
        .dropna(subset=["date"])
        .set_index("date")
        .sort_index()
    )


def get_series_info(series_id: str) -> dict:
    """
    Get information about a FRED series.

    This includes things such as:
    title, frequency, units, and seasonal adjustment.
    """

    # Ask FRED for metadata about the series
    payload = fred_get("series", {"series_id": series_id})

    # FRED calls the metadata list "seriess"
    series = payload.get("seriess", [])

    # Stop if no metadata was found
    if not series:
        raise ValueError(f"No metadata found for {series_id}")

    # Return the first matching series
    return series[0]


def get_vintage(
    series_id: str,
    vintage_date: str,
    observation_start: str,
) -> pd.DataFrame:
    """
    Get a historical version of a FRED series.

    This lets us ask:
    What did this economic data look like on a specific past date?
    """

    # Request the data exactly as it was available on vintage_date
    payload = fred_get(
        "series/observations",
        {
            "series_id": series_id,
            "observation_start": observation_start,
            "realtime_start": vintage_date,
            "realtime_end": vintage_date,
        },
    )

    # Convert the returned observations into a DataFrame
    frame = pd.DataFrame(payload["observations"])

    # Convert dates from text into datetime values
    frame["date"] = pd.to_datetime(frame["date"])

    # Convert the values from text into numbers
    frame[series_id] = pd.to_numeric(frame["value"], errors="coerce")

    # Keep only the date and economic series
    return frame[["date", series_id]].set_index("date")


# ============================================================
# REAL GDP DATA
# ============================================================

# Download Real GDP data starting in 2000
gdp = get_series("GDPC1", observation_start="2000-01-01")

# Rename the FRED series ID to something easier to understand
gdp = gdp.rename(columns={"GDPC1": "Real GDP"})

# ============================================================
# CALCULATING REAL GDP
# ============================================================

gdp["Real GDP Growth YoY"] = (
    gdp["Real GDP"].pct_change(periods=4, fill_method=None) * 100
)

# Show the five most recent GDP observations
print("\nReal GDP:")
print(gdp.tail())

# ============================================================
# MONTHLY ECONOMIC DATA
# ============================================================

# FRED series IDs mapped to easier column names
SERIES = {
    "CPIAUCSL": "CPI",
    "UNRATE": "Unemployment Rate",
    "FEDFUNDS": "Federal Funds Rate",
}

# This list will temporarily store each DataFrame
frames = []

# Download every series listed above
for series_id, label in SERIES.items():

    # Download the series
    frame = get_series(series_id, observation_start="2000-01-01")

    # Rename the column from the FRED ID to our readable label
    frame = frame.rename(columns={series_id: label})

    # Add the DataFrame to our list
    frames.append(frame)


# Combine CPI, unemployment, and interest rates into one table
# axis=1 means combine them side by side using their dates
monthly = pd.concat(frames, axis=1).sort_index()


# ============================================================
# CALCULATE INFLATION
# ============================================================

# Calculate year-over-year inflation
# CPI is monthly, so 12 periods means comparing with 12 months earlier
monthly["Inflation YoY"] = (
    monthly["CPI"].pct_change(periods=12, fill_method=None) * 100
)


# ============================================================
# ANALYSIS TABLE
# ============================================================

# Create a smaller table containing the indicators we want to analyze
analysis = monthly[
    ["Inflation YoY", "Unemployment Rate", "Federal Funds Rate"]
].dropna(how="all")


# Calculate summary statistics for each economic indicator
summary = analysis.agg(
    ["count", "mean", "min", "median", "max"]
).T


# Find the newest available value for each indicator
summary["latest"] = analysis.apply(
    lambda series: series.dropna().iloc[-1]
)


# Find the date of the newest available value for each indicator
summary["latest_date"] = [
    analysis[column].last_valid_index().date()
    for column in analysis.columns
]


# Print the summary table rounded to two decimal places
print(summary.round(2))


# ============================================================
# GRAPH 1
# INFLATION VS UNEMPLOYMENT
# ============================================================

# Keep only inflation and unemployment rows where both values exist
plot_data = analysis[
    ["Inflation YoY", "Unemployment Rate"]
].dropna()


# Create the graph
fig, ax = plt.subplots(figsize=(11, 6))


# Plot inflation
ax.plot(
    plot_data.index,
    plot_data["Inflation YoY"],
    label="CPI inflation, YoY",
)


# Plot unemployment
ax.plot(
    plot_data.index,
    plot_data["Unemployment Rate"],
    label="Unemployment rate",
)


# Draw a horizontal line at 0%
ax.axhline(0, linewidth=0.8)


# Add graph labels
ax.set_title("U.S. Inflation and Unemployment")
ax.set_xlabel("Date")
ax.set_ylabel("Percent")


# Add a legend and grid
ax.legend()
ax.grid(alpha=0.25)


# Adjust spacing so nothing gets cut off
fig.tight_layout()


# Display the graph
plt.show()


# ============================================================
# GRAPH 2
# REAL GDP
# ============================================================

# Create a second graph
fig, ax = plt.subplots(figsize=(11, 6))


# Plot Real GDP
ax.plot(gdp.index, gdp["Real GDP"])


# Add graph labels
ax.set_title("U.S. Real GDP")
ax.set_xlabel("Date")
ax.set_ylabel("Billions of Chained 2017 Dollars")


# Add grid lines
ax.grid(alpha=0.25)


# Adjust spacing
fig.tight_layout()


# Display the GDP graph
plt.show()


# ============================================================
# QUARTERLY UNEMPLOYMENT
# ============================================================

# Ask FRED to convert monthly unemployment into quarterly averages
quarterly_params = {
    "series_id": "UNRATE",
    "frequency": "q",
    "aggregation_method": "avg",
}


# Download the quarterly unemployment data
quarterly_data = fred_get(
    "series/observations",
    quarterly_params,
)


# Convert the observations into a DataFrame
quarterly_df = pd.DataFrame(
    quarterly_data["observations"]
)


# Convert dates from text into datetime values
quarterly_df["date"] = pd.to_datetime(
    quarterly_df["date"]
)


# Convert unemployment values from text into numbers
quarterly_df["value"] = pd.to_numeric(
    quarterly_df["value"],
    errors="coerce",
)


# Print the five newest quarterly unemployment values
print("\nQuarterly unemployment:")
print(
    quarterly_df[["date", "value"]].tail()
)


# ============================================================
# HISTORICAL GDP VINTAGE COMPARISON
# ============================================================

# Get GDP as it was known on July 27, 2023
old = get_vintage(
    "GDPC1",
    "2023-07-27",
    "2018-01-01",
)


# Get GDP as it was known on July 25, 2024
new = get_vintage(
    "GDPC1",
    "2024-07-25",
    "2018-01-01",
)


# Put the two historical versions next to each other
comparison = pd.concat(
    [
        old.rename(columns={"GDPC1": "old"}),
        new.rename(columns={"GDPC1": "new"}),
    ],
    axis=1,
)


# Calculate how much each GDP value changed between the two vintages
comparison["revision"] = (
    comparison["new"] - comparison["old"]
)


# Print the ten newest rows
print("\nGDP vintage comparison:")
print(comparison.tail(10))


# ============================================================
# DATA VALIDATION
# ============================================================

# Make sure dates are ordered from oldest to newest
assert monthly.index.is_monotonic_increasing


# Make sure there are no duplicate dates
assert not monthly.index.duplicated().any()


# Make sure every CPI value is greater than zero
assert (
    monthly["CPI"]
    .dropna()
    .gt(0)
    .all()
)


# Make sure unemployment values are between 0% and 100%
assert (
    monthly["Unemployment Rate"]
    .dropna()
    .between(0, 100)
    .all()
)


# If the program reaches this point, all validation tests passed
print("\nAll validation checks passed.")