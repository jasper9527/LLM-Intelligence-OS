from intel import load_events, load_routing_config, route_event, save_events


def main() -> None:
    routing = load_routing_config()
    events = [route_event(event, routing) for event in load_events()]
    save_events(events)
    print(f"routed={len(events)}")


if __name__ == "__main__":
    main()
