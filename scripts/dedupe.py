from intel import dedupe_events, load_events, save_events, update_review_summary


def main() -> None:
    save_events(dedupe_events(load_events()))
    update_review_summary()
    print("deduped=1")


if __name__ == "__main__":
    main()
