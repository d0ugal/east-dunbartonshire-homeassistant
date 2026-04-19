"""Constants for the Scottish Bins integration."""

DOMAIN = "scottish_bins"

CONF_COUNCIL = "council"
CONF_UPRN = "uprn"
CONF_ADDRESS = "address"

COUNCIL_EAST_DUNBARTONSHIRE = "east_dunbartonshire"
COUNCIL_CLACKMANNANSHIRE = "clackmannanshire"
COUNCIL_FALKIRK = "falkirk"

COUNCILS = {
    COUNCIL_EAST_DUNBARTONSHIRE: "East Dunbartonshire",
    COUNCIL_CLACKMANNANSHIRE: "Clackmannanshire",
    COUNCIL_FALKIRK: "Falkirk",
}

# Bin-type key → display name for each council.
# For East Dunbartonshire the keys are HTML CSS classes.
# For Clackmannanshire the keys match the ICS SUMMARY field.
# For Falkirk the keys match the API "type" field.
COUNCIL_BINS: dict[str, dict[str, str]] = {
    COUNCIL_EAST_DUNBARTONSHIRE: {
        "food-caddy": "Food caddy",
        "garden-bin": "Green bin",
        "rubbish-bin": "Grey bin",
    },
    COUNCIL_CLACKMANNANSHIRE: {
        "Grey bin": "Grey bin",
        "Green bin": "Green bin",
        "Blue bin": "Blue bin",
        "Food caddy": "Food caddy",
    },
    COUNCIL_FALKIRK: {
        "Food caddy": "Food caddy",
        "Blue bin": "Blue bin",
        "Green bin": "Green bin",
        "Burgundy bin": "Burgundy bin",
        "Black box": "Black box",
        "Brown bin": "Brown bin",
    },
}
