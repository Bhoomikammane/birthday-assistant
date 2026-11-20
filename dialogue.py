def enrich_with_context(parsed, state):
    """
    Add previous conversation context
    when the current question does not contain it.
    """

    entities = parsed["entities"]

    # Carry forward month and relationship
    for key in ("month", "relationship"):

        if key not in entities and state.get(key) is not None:

            entities[key] = state[key]

    return parsed


def update_state(parsed, state, last_result_ids=None):
    """
    Save useful information from the current conversation.
    """

    entities = parsed["entities"]

    # Save useful entities
    for key in (
        "month",
        "relationship",
        "person_id",
        "person_name"
    ):

        if key in entities:
            state[key] = entities[key]

    # Save matching person IDs when needed
    if last_result_ids is not None:

        state["last_result_ids"] = last_result_ids

    return state