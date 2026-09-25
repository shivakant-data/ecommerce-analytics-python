from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

FILE = Path("ecommerce_data_12000.csv")
OUTPUT = Path("screenshots")


def load_data():
    df = pd.read_csv(FILE)
    df = df.drop_duplicates(subset="Order_ID", keep="first")

    for col in [
        "Category", "Product", "City",
        "Payment_Method", "Order_Status", "Returned"
    ]:
        df[col] = df[col].astype("string").str.strip()

    for col in ["Sales", "Profit", "Quantity", "Customer_Rating"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Order_Date"] = pd.to_datetime(
        df["Order_Date"], errors="coerce"
    )
    df["Return_Flag"] = df["Returned"].map(
        {"Yes": 1, "No": 0}
    ).astype("Int64")

    return df[df["Order_Status"].eq("Delivered")].copy()


def save_chart(filename):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(
        OUTPUT / filename,
        dpi=180,
        bbox_inches="tight"
    )
    plt.close()


def main():
    df = load_data()

    monthly = df.groupby(
        df["Order_Date"].dt.to_period("M").astype(str)
    )["Sales"].sum()

    monthly.plot(
        figsize=(10, 5),
        title="Monthly Sales Trend"
    )
    plt.xlabel("Month")
    plt.ylabel("Sales (₹)")
    plt.xticks(rotation=45)
    save_chart("monthly_sales_trend.png")

    category = (
        df.groupby("Category")["Sales"]
        .sum()
        .sort_values()
    )

    category.plot(
        kind="barh",
        figsize=(9, 5),
        title="Sales by Category"
    )
    plt.xlabel("Sales (₹)")
    plt.ylabel("Category")
    save_chart("sales_by_category.png")

    city = (
        df.groupby("City")["Profit"]
        .sum()
        .sort_values()
        .tail(10)
    )

    city.plot(
        kind="barh",
        figsize=(9, 6),
        title="Top 10 Cities by Profit"
    )
    plt.xlabel("Profit (₹)")
    plt.ylabel("City")
    save_chart("profit_by_city.png")

    category_return = (
        df.groupby("Category")["Return_Flag"]
        .mean()
        .mul(100)
        .sort_values()
    )

    category_return.plot(
        kind="barh",
        figsize=(9, 5),
        title="Return Rate by Category"
    )
    plt.xlabel("Return Rate (%)")
    plt.ylabel("Category")
    save_chart("return_rate_by_category.png")

    payment = (
        df.groupby("Payment_Method")["Sales"]
        .sum()
        .sort_values()
    )

    payment.plot(
        kind="barh",
        figsize=(9, 5),
        title="Sales by Payment Method"
    )
    plt.xlabel("Sales (₹)")
    plt.ylabel("Payment Method")
    save_chart("sales_by_payment_method.png")

    plt.figure(figsize=(9, 5))
    plt.scatter(
        df["Quantity"],
        df["Sales"],
        alpha=0.25
    )
    plt.title("Quantity vs Sales")
    plt.xlabel("Quantity")
    plt.ylabel("Sales (₹)")
    save_chart("quantity_vs_sales.png")

    print(
        "6 e-commerce charts generated successfully "
        "in the screenshots folder."
    )


if __name__ == "__main__":
    main()
