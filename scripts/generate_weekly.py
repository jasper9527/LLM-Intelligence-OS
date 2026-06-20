from intel import generate_weekly_report


def main() -> None:
    report = generate_weekly_report()
    print(report["report_id"])


if __name__ == "__main__":
    main()
