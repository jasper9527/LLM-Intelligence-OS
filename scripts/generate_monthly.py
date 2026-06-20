from intel import generate_monthly_report


def main() -> None:
    report = generate_monthly_report()
    print(report["report_id"])


if __name__ == "__main__":
    main()
