from intel import import_codex_candidates


if __name__ == "__main__":
    result = import_codex_candidates()
    print(", ".join(f"{key}={value}" for key, value in result.items()))
