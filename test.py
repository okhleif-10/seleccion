from logic import fetch_team_squad, load_fifa_rankings, fetch_wikipedia_page, extract_squad_table

def test_entire_workflow():
    nations = load_fifa_rankings()
    passed = []
    failed = []
    for nation in nations["country_full"]:
        try:
            fetch_team_squad(nation)
            print(nation, " PASSED")
            passed.append(nation)
        except Exception:
            print(nation, " FAILED")
            failed.append(failed)

    print(f"\nTotal PASSED: {len(passed)} / {len(nations)}")
    print(f"\nTotal FAILED: {len(failed)} / {len(nations)}")
    if failed:
        print("Failures:", failed)

def test_squad_tables():
    nations = load_fifa_rankings()
    passed = []
    failed = []
    nations = nations["country_full"]
    for nation in nations:
        html, soup = fetch_wikipedia_page(nation)
        if not html:
            print(f"❌ FAILED: Could not fetch: {nation}")
            failed.append(nation)
            continue

        table = extract_squad_table(soup)
        if table is None:
            print(f"❌ FAILED: No squad table found for: {nation}")
            failed.append(nation)
        else:
            print(f"✅ {nation} PASSED")
            passed.append(nation)

    print(f"\nTotal PASSED: {len(passed)} / {len(nations)}")
    print(f"\nTotal FAILED: {len(failed)} / {len(nations)}")
    if failed:
        print("Failures:", failed)


if __name__ == '__main__':
    # test_entire_workflow()
    test_squad_tables()