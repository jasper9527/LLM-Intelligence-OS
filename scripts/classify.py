from intel import classify_event, load_candidate_tags, load_events, save_candidate_tags, save_events, taxonomy_sets


def main() -> None:
    events = load_events()
    taxonomy = taxonomy_sets()
    candidates = load_candidate_tags()
    classified = []
    for event in events:
        event, new_candidates = classify_event(event, taxonomy)
        classified.append(event)
        candidates.extend(new_candidates)
    save_events(classified)
    save_candidate_tags(candidates)
    print(f"classified={len(classified)}")


if __name__ == "__main__":
    main()
