from rise_engine.services import detect_service_points, is_service_sheet

SHEET = (
    "EE1 EE2 NE1 SE1 EP1 EP2 NP1\n"
    "Existing Electrical - EE    Existing Plumbing - EP\n"
    "New Electrical - NE    New Plumbing - NP\n"
    "Shifted Electrical - SE    Shifted Plumbing - SP\n"
)


def test_is_service_sheet():
    assert is_service_sheet(SHEET)
    assert not is_service_sheet("Cabinet Code Carcass Shutter Sizes Hardware Details")


def test_detect_service_points_counts_distinct():
    elec, plumb = detect_service_points(SHEET)
    assert elec == {"EE1", "EE2", "NE1", "SE1"}
    assert plumb == {"EP1", "EP2", "NP1"}


def test_non_service_sheet_returns_empty():
    # Even if a stray code appears, without the legend we don't count it.
    elec, plumb = detect_service_points("random EE1 text without legend")
    assert elec == set() and plumb == set()


def test_duplicate_codes_counted_once():
    text = SHEET + "\nEE1 EE1 NE1"  # markers repeated
    elec, _ = detect_service_points(text)
    assert elec == {"EE1", "EE2", "NE1", "SE1"}
