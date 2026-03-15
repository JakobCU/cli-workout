"""Big digit renderer for the workout timer display."""

_DIGIT_ART = {
    "0": [
        " ######  ",
        "##    ## ",
        "##    ## ",
        "##    ## ",
        "##    ## ",
        "##    ## ",
        " ######  ",
    ],
    "1": [
        "   ##    ",
        " ####    ",
        "   ##    ",
        "   ##    ",
        "   ##    ",
        "   ##    ",
        " ######  ",
    ],
    "2": [
        " ######  ",
        "##    ## ",
        "      ## ",
        "  ####   ",
        "##       ",
        "##       ",
        "######## ",
    ],
    "3": [
        " ######  ",
        "##    ## ",
        "      ## ",
        "  #####  ",
        "      ## ",
        "##    ## ",
        " ######  ",
    ],
    "4": [
        "##    ## ",
        "##    ## ",
        "##    ## ",
        "######## ",
        "      ## ",
        "      ## ",
        "      ## ",
    ],
    "5": [
        "######## ",
        "##       ",
        "##       ",
        "#######  ",
        "      ## ",
        "##    ## ",
        " ######  ",
    ],
    "6": [
        " ######  ",
        "##       ",
        "##       ",
        "#######  ",
        "##    ## ",
        "##    ## ",
        " ######  ",
    ],
    "7": [
        "######## ",
        "      ## ",
        "     ##  ",
        "    ##   ",
        "   ##    ",
        "   ##    ",
        "   ##    ",
    ],
    "8": [
        " ######  ",
        "##    ## ",
        "##    ## ",
        " ######  ",
        "##    ## ",
        "##    ## ",
        " ######  ",
    ],
    "9": [
        " ######  ",
        "##    ## ",
        "##    ## ",
        " ####### ",
        "      ## ",
        "      ## ",
        " ######  ",
    ],
    ":": [
        "         ",
        "   ##    ",
        "   ##    ",
        "         ",
        "   ##    ",
        "   ##    ",
        "         ",
    ],
}

# Flame deco lines that cycle around the timer
_FLAME_FRAMES = [
    r"  )  ) )  )  ) )  )  ) )  )  ) )  )  ) )  ",
    r" (  ( (  (  ( (  (  ( (  (  ( (  (  ( (  (  ",
    r"  )  ) )  )  ) )  )  ) )  )  ) )  )  ) )  ) ",
    r" (  ( (  (  ( (  (  ( (  (  ( (  (  ( (  (   ",
]

_EMBER_FRAMES = [
    r"  . * . ' . * . ' . * . ' . * . ' . * . '  ",
    r"  ' . * . ' . * . ' . * . ' . * . ' . * .  ",
    r"  * ' . * ' . * ' . * ' . * ' . * ' . * '  ",
    r"  . ' * . ' * . ' * . ' * . ' * . ' * . '  ",
]


def render_big_time(seconds, tick_count=0):
    """Render MM:SS as large block digits with animated flame border."""
    m, s = divmod(int(seconds), 60)
    time_str = f"{m:02d}:{s:02d}"

    # Build the 7 lines by concatenating digit art
    lines = []
    for row in range(7):
        line = ""
        for ch in time_str:
            line += _DIGIT_ART.get(ch, _DIGIT_ART["0"])[row]
        lines.append(line)

    # Add flame decorations
    flame = _FLAME_FRAMES[tick_count % len(_FLAME_FRAMES)]
    ember = _EMBER_FRAMES[tick_count % len(_EMBER_FRAMES)]

    result = []
    result.append(flame)
    result.append("")
    for line in lines:
        result.append(f"    {line}")
    result.append("")
    result.append(ember)
    return "\n".join(result)
