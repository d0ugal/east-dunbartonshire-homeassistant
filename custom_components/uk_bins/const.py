"""Constants for the UK Bins integration."""

DOMAIN = "uk_bins"

CONF_COUNCIL = "council"
CONF_UPRN = "uprn"
CONF_ADDRESS = "address"

COUNCIL_CLACKMANNANSHIRE = "clackmannanshire"
COUNCIL_EAST_DUNBARTONSHIRE = "east_dunbartonshire"
COUNCIL_EAST_RENFREWSHIRE = "east_renfrewshire"
COUNCIL_FALKIRK = "falkirk"
COUNCIL_NORTH_AYRSHIRE = "north_ayrshire"
COUNCIL_SOUTH_AYRSHIRE = "south_ayrshire"
COUNCIL_WEST_LOTHIAN = "west_lothian"

COUNCILS = {
    COUNCIL_CLACKMANNANSHIRE: "Clackmannanshire",
    COUNCIL_EAST_DUNBARTONSHIRE: "East Dunbartonshire",
    COUNCIL_EAST_RENFREWSHIRE: "East Renfrewshire",
    COUNCIL_FALKIRK: "Falkirk",
    COUNCIL_NORTH_AYRSHIRE: "North Ayrshire",
    COUNCIL_SOUTH_AYRSHIRE: "South Ayrshire",
    COUNCIL_WEST_LOTHIAN: "West Lothian",
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
    COUNCIL_NORTH_AYRSHIRE: {
        "blue_bin": "Blue bin",
        "grey_bin": "Grey bin",
        "purple_bin": "Purple bin",
        "brown_bin": "Brown bin",
    },
    COUNCIL_EAST_RENFREWSHIRE: {
        "Blue bin": "Blue bin",
        "Brown bin": "Brown bin",
        "Green bin": "Green bin",
        "Grey bin": "Grey bin",
    },
    COUNCIL_SOUTH_AYRSHIRE: {
        "Blue/Blue Lidded Bin": "Blue bin",
        "Brown Bin": "Brown bin",
        "Food Waste Caddy": "Food caddy",
        "Green/Green Lidded Bin": "Green bin",
    },
    COUNCIL_WEST_LOTHIAN: {
        "BLUE": "Blue bin",
        "GREY": "Grey bin",
        "BROWN": "Brown bin",
        "GREEN": "Green bin",
    },
}
