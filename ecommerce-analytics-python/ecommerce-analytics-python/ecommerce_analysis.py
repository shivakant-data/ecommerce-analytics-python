from pathlib import Path
import numpy as np
import pandas as pd

FILE = Path("ecommerce_data_12000.csv")
CLEANED_FILE = Path("ecommerce_data_cleaned.csv")

SUMMARY_FILES = {
    "customer": Path("customer_summary.csv"),
    "category": Path("category_summary.csv"),
    "city": Path("city_summary.csv"),
    "monthly": Path("monthly_summary.csv"),
    "payment": Path("payment_summary.csv"),
    "rfm": Path("rfm_summary.csv"),
}

def clean_data(df):
    df = df.copy()
    df = df.drop_duplicates(subset="Order_ID", keep="first")

    text_cols = [
        "Gender", "City", "State", "Category", "Product",
        "Payment_Method", "Order_Status", "Returned"
    ]
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()

    numeric_cols = [
        "Age", "Quantity", "Unit_Price", "Discount_Pct",
        "Sales", "Cost", "Profit", "Delivery_Days",
        "Customer_Rating"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    df["Payment_Method"] = df["Payment_Method"].fillna("Unknown")
    df["Customer_Rating"] = df["Customer_Rating"].fillna(
        df["Customer_Rating"].median()
    )
    df["Delivery_Days"] = df["Delivery_Days"].fillna(
        df["Delivery_Days"].median()
    )

    df["Profit_Margin_Pct"] = np.where(
        df["Sales"].ne(0),
        df["Profit"] / df["Sales"] * 100,
        0
    )
    df["Month"] = df["Order_Date"].dt.to_period("M").astype(str)
    df["Return_Flag"] = df["Returned"].map(
        {"Yes": 1, "No": 0}
    ).astype("Int64")

    return df


def rfm_analysis(df):
    snapshot = df["Order_Date"].max() + pd.Timedelta(days=1)
    delivered = df[df["Order_Status"].eq("Delivered")].copy()

    rfm = delivered.groupby("Customer_ID").agg(
        Recency=("Order_Date", lambda x: (snapshot - x.max()).days),
        Frequency=("Order_ID", "nunique"),
        Monetary=("Sales", "sum"),
    )

    rfm["R_Score"] = pd.qcut(
        rfm["Recency"].rank(method="first"),
        5,
        labels=[5, 4, 3, 2, 1]
    ).astype(int)

    rfm["F_Score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["M_Score"] = pd.qcut(
        rfm["Monetary"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["RFM_Score"] = (
        rfm["R_Score"].astype(str)
        + rfm["F_Score"].astype(str)
        + rfm["M_Score"].astype(str)
    )

    def segment(row):
        if row["R_Score"] >= 4 and row["F_Score"] >= 4 and row["M_Score"] >= 4:
            return "Champions"
        if row["R_Score"] >= 4 and row["F_Score"] >= 3:
            return "Loyal Customers"
        if row["R_Score"] >= 4 and row["F_Score"] <= 2:
            return "New Customers"
        if row["R_Score"] <= 2 and row["F_Score"] >= 3:
            return "At Risk"
        if row["R_Score"] <= 2 and row["M_Score"] <= 2:
            return "Lost Customers"
        return "Potential Loyalists"

    rfm["Segment"] = rfm.apply(segment, axis=1)
    return rfm


def main():
    if not FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {FILE}")

    raw = pd.read_csv(FILE)
    df = clean_data(raw)

    print("=" * 70)
    print("E-COMMERCE ANALYTICS - DATA QUALITY")
    print("=" * 70)
    print(f"Raw rows: {len(raw):,}")
    print(f"Clean rows: {len(df):,}")
    print(
        f"Duplicate orders removed: "
        f"{raw['Order_ID'].duplicated().sum():,}"
    )
    print(
        f"Remaining missing cells: "
        f"{int(df.isna().sum().sum()):,}"
    )

    delivered = df[df["Order_Status"].eq("Delivered")]

    total_sales = delivered["Sales"].sum()
    total_profit = delivered["Profit"].sum()
    orders = delivered["Order_ID"].nunique()
    customers = delivered["Customer_ID"].nunique()
    aov = total_sales / orders if orders else 0
    margin = total_profit / total_sales * 100 if total_sales else 0
    return_rate = delivered["Return_Flag"].mean() * 100

    print("\n" + "=" * 70)
    print("OVERALL E-COMMERCE KPIs")
    print("=" * 70)
    print(f"Delivered Orders: {orders:,}")
    print(f"Unique Customers: {customers:,}")
    print(f"Total Sales: ₹{total_sales:,.0f}")
    print(f"Total Profit: ₹{total_profit:,.0f}")
    print(f"Average Order Value: ₹{aov:,.2f}")
    print(f"Overall Profit Margin: {margin:.2f}%")
    print(f"Return Rate: {return_rate:.2f}%")
    print(
        f"Average Rating: "
        f"{delivered['Customer_Rating'].mean():.2f}/5"
    )

    customer = delivered.groupby("Customer_ID").agg(
        Orders=("Order_ID", "nunique"),
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Avg_Order_Value=("Sales", "mean"),
        Avg_Rating=("Customer_Rating", "mean"),
    ).sort_values("Sales", ascending=False)

    category = delivered.groupby("Category").agg(
        Orders=("Order_ID", "nunique"),
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Avg_Order_Value=("Sales", "mean"),
        Return_Rate=("Return_Flag", "mean"),
    )
    category["Return_Rate"] *= 100
    category = category.sort_values("Sales", ascending=False)

    city = delivered.groupby("City").agg(
        Orders=("Order_ID", "nunique"),
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Avg_Order_Value=("Sales", "mean"),
    ).sort_values("Sales", ascending=False)

    monthly = delivered.groupby("Month").agg(
        Orders=("Order_ID", "nunique"),
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
    )

    payment = delivered.groupby("Payment_Method").agg(
        Orders=("Order_ID", "nunique"),
        Sales=("Sales", "sum"),
        Avg_Order_Value=("Sales", "mean"),
    ).sort_values("Sales", ascending=False)

    rfm = rfm_analysis(df)
    rfm_summary = rfm.groupby("Segment").agg(
        Customers=("Monetary", "size"),
        Avg_Recency=("Recency", "mean"),
        Avg_Frequency=("Frequency", "mean"),
        Total_Monetary=("Monetary", "sum"),
    ).sort_values("Total_Monetary", ascending=False)

    print("\n" + "=" * 70)
    print("TOP BUSINESS SIGNALS")
    print("=" * 70)
    print(f"Top category by sales: {category['Sales'].idxmax()}")
    print(f"Top city by sales: {city['Sales'].idxmax()}")
    print(f"Top payment method by sales: {payment['Sales'].idxmax()}")
    print(f"Top customer by sales: {customer['Sales'].idxmax()}")
    print(f"Highest-profit category: {category['Profit'].idxmax()}")
    print(
        f"Highest return-rate category: "
        f"{category['Return_Rate'].idxmax()}"
    )

    df.to_csv(CLEANED_FILE, index=False)
    customer.to_csv(SUMMARY_FILES["customer"])
    category.to_csv(SUMMARY_FILES["category"])
    city.to_csv(SUMMARY_FILES["city"])
    monthly.to_csv(SUMMARY_FILES["monthly"])
    payment.to_csv(SUMMARY_FILES["payment"])
    rfm_summary.to_csv(SUMMARY_FILES["rfm"])

    print(
        "\nAnalysis complete. "
        "Summary CSV files exported successfully."
    )


if __name__ == "__main__":
    main()
