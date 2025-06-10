import pandas as pd


def analyze_locust_log(csv_file):
    # Load CSV log
    df = pd.read_csv(csv_file)

    # Group by endpoint (name column in Locust CSV)
    grouped = (
        df.groupby("Name")
        .agg(
            {
                "Request Count": "sum",
                "Failure Count": "sum",
                "Median Response Time": "mean",
                "Average Response Time": "mean",
                "Requests/s": "mean",
            }
        )
        .reset_index()
    )

    # Calculate failure rate
    grouped["Failure Rate (%)"] = (
        grouped["Failure Count"] / grouped["Request Count"]
    ) * 100

    # Determine the optimal endpoint
    # - lowest average response time
    # - highest requests/sec
    # - lowest failure rate
    optimal = grouped.sort_values(
        by=["Failure Rate (%)", "Average Response Time", "Requests/s"],
        ascending=[True, True, False],
    ).iloc[0]

    print("\n🟢 Locust Performance Summary:")
    print(grouped.to_string(index=False))

    print("\n🏆 Optimal endpoint suggestion:")
    print(f"  Endpoint: {optimal['Name']}")
    print(f"  Average Response Time: {optimal['Average Response Time']:.2f} ms")
    print(f"  Requests/s: {optimal['Requests/s']:.2f}")
    print(f"  Failure Rate: {optimal['Failure Rate (%)']:.2f}%")


if __name__ == "__main__":
    csv_file = "locust_stats_history.csv"  # Change this to your actual Locust CSV file
    analyze_locust_log(csv_file)
