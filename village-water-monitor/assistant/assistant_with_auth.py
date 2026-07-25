"""
assistant_with_auth.py
-----------------------
Task 3: the user identifies themselves, and the assistant answers ONLY
from that person's own records (their own habitation), never anyone else's.

Interpretation used here: each user is a panchayat worker responsible for
ONE habitation. When they ask a question, their view of the data is
filtered down to only their habitation before any intent logic runs.

This file builds on assistant.py (Task 2) rather than duplicating it -
same intents, same matching, just with a data-filtering step in front.
"""

from assistant import (
    load_data, normalize_input, extract_waterpoint_id,
    intent_is_working, intent_downtime_duration, intent_list_down,
    intent_usage_count, intent_habitation_most_down, SUPPORTED_QUESTIONS
)

# ---------------------------------------------------------------------
# User registry: maps username -> habitation they're responsible for
# In a real deployment this would be a proper login system; for this
# simulation a simple lookup table is enough.
# ---------------------------------------------------------------------

USER_REGISTRY = {
    "officer_kollam": "Kollampalayam",
    "officer_sunda": "Sundapatti",
    "officer_marudur": "Marudur",
    "officer_perumb": "Perumbakkam",
}


def get_user_habitation(username):
    """Returns the habitation a user is allowed to see, or None if unknown user."""
    return USER_REGISTRY.get(username)


def filter_to_user_habitation(data, habitation):
    """Only the rows belonging to this user's habitation - this is the
    privacy boundary. No intent function ever sees another habitation's data."""
    return [r for r in data if r["habitation"] == habitation]


def waterpoint_belongs_to_user(data, waterpoint_id, habitation):
    """Check a requested waterpoint actually belongs to the user's habitation,
    so someone can't ask about a specific WP id outside their own area."""
    return any(r["waterpoint_id"] == waterpoint_id and r["habitation"] == habitation
               for r in data)


# ---------------------------------------------------------------------
# Authenticated intent matching
# ---------------------------------------------------------------------

def ask(username, raw_text, full_data):
    # Step 1: identify the user
    habitation = get_user_habitation(username)
    if habitation is None:
        return f"Unknown user '{username}'. I can't answer without a recognised login."

    # Step 2: scope data to only this user's habitation
    user_data = filter_to_user_habitation(full_data, habitation)

    # Step 3: normal intent matching, but constrained to user_data only
    text = normalize_input(raw_text)
    wp_id = extract_waterpoint_id(text)

    # If they asked about a specific waterpoint outside their habitation,
    # refuse rather than silently answering from the full dataset.
    if wp_id and not waterpoint_belongs_to_user(full_data, wp_id, habitation):
        return (f"I can only answer questions about waterpoints in {habitation}. "
                f"{wp_id} is not in your area.")

    if wp_id and any(k in text for k in ["working", "status", "is up", "is it down"]):
        return intent_is_working(user_data, wp_id)

    if wp_id and any(k in text for k in ["how long", "down for", "since when"]):
        return intent_downtime_duration(user_data, wp_id)

    if any(k in text for k in ["which waterpoints are down", "list down", "currently down", "all down"]):
        return intent_list_down(user_data)

    if wp_id and any(k in text for k in ["usage", "how many times", "draw", "drawn"]):
        return intent_usage_count(user_data, wp_id)

    if any(k in text for k in ["which habitation", "most down", "habitation with"]):
        # This intent is inherently cross-habitation (a comparison), so it
        # is out of scope for a single-habitation officer - refuse cleanly
        # rather than leak other habitations' data.
        return ("That question compares across habitations, which is outside "
                "what I can show you for your area. I can tell you about your "
                f"own habitation ({habitation}) instead - try 'list down waterpoints'.")

    listing = "\n  - ".join(SUPPORTED_QUESTIONS)
    return ("I'm not confident I understood that question. Here is what I can answer:\n  - " + listing)


# ---------------------------------------------------------------------
# Manual test: two different users, confirm isolation + refusal
# ---------------------------------------------------------------------

if __name__ == "__main__":
    data = load_data()

    print("=== User: officer_kollam (Kollampalayam) ===")
    print(ask("officer_kollam", "list down waterpoints", data), "\n")
    print(ask("officer_kollam", "is wp001 working", data), "\n")
    # Try to peek at another habitation's waterpoint - should be refused
    print(ask("officer_kollam", "is wp004 working", data), "\n")

    print("=== User: officer_sunda (Sundapatti) ===")
    print(ask("officer_sunda", "list down waterpoints", data), "\n")
    print(ask("officer_sunda", "is wp004 working", data), "\n")

    print("=== Unknown user ===")
    print(ask("random_person", "is wp001 working", data), "\n")

    print("=== Cross-habitation question (should refuse) ===")
    print(ask("officer_kollam", "which habitation has the most down waterpoints", data), "\n")

    print("=== Out-of-scope question (should list supported questions) ===")
    print(ask("officer_kollam", "what is the weather today", data))