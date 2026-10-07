"""Shot list: frames sum to 720 at 24 fps. Cut points land on multiples of 12 (one beat at 120 BPM)."""
COMPACT = ("candid camera-roll photo, 35mm lens, natural light, shallow depth of field, subtle film grain, "
           "cinematic, photorealistic, seen from behind, faceless")
NEG = ("text, letters, words, logos, brand names, watermark, captions, license plates, signage, UI elements, "
       "face, eyes, looking at camera, portrait, money, cash, cartoon, illustration, painting, 3d render, "
       "deformed hands, extra fingers, blurry, lowres, numbers, emblem, badge, dial markings")
PHASE = {
    "A": "cold blue and teal tones, desaturated, dark",
    "B": "cool blue light turning warm, warm golden light spilling in",
    "C": "warm golden hour light, amber and teal, rich contrast",
    "Cn": "night, deep blue and warm amber city lights",
    "D": "soft warm golden light, calm and still",
}
# (id, frames, phase, subject, motion, transition_in)
SHOTS = [
    (1, 48, "A", "POV hands typing on a laptop in a dark room at 3am, screen glow lighting the hands, blurred city lights through window behind", "push_in", "grid_zoom"),
    (2, 36, "A", "rain streaking down a floor-to-ceiling window at night, blurred city lights bokeh, distant lightning flash, empty dark apartment", "drift", "cut"),
    (3, 36, "A", "side view of a hand pressing a laptop screen half closed, lid nearly shut, thin sliver of screen glow, dark desk at night", "push_in_slow", "cut"),
    (4, 36, "B", "hand pushing open a private jet cabin door, bright warm golden sunlight flooding in, airstairs below, tarmac", "push_in", "match_cut"),
    (5, 24, "B", "luxury leather luggage and a duffel bag beside a black SUV on a private jet tarmac at dusk, jet in background", "slide_left", "light_leak"),
    (6, 36, "B", "private jet cabin interior, cream leather seats, fruit plate on table, dark silhouette of a young man seated by the oval window, seen from behind", "orbit", "cut"),
    (7, 24, "Cn", "low front three-quarter view of a black car, sleek glowing LED headlights at night, smooth hood, rain-wet reflective pavement, bokeh", "push_in", "whip"),
    (8, 24, "B", "POV laptop on a white table on a yacht deck, turquoise sea and rocky coastline through the window, sunlight", "slide_right", "cut"),
    (9, 24, "B", "silhouette of a young man standing at a penthouse floor-to-ceiling window, huge city skyline at sunset, seen from behind", "pull_out", "light_leak"),
    (10, 12, "C", "POV hand holding a small white espresso cup, plain steel bracelet watch seen from the side, stone table, morning sun", "push_in", "cut"),
    (11, 12, "C", "black sports car and black boxy luxury SUV parked on a stone driveway under golden autumn trees, mansion", "slide_left", "cut"),
    (12, 24, "C", "infinity pool edge overlooking a futuristic coastal skyline at sunset, two distant silhouettes on loungers, palm leaf foreground", "slide_right", "whip"),
    (13, 24, "C", "back of head of a young man with dark curly hair, laptop on knees, over-the-shoulder view from behind, cliffside Mediterranean balcony, turquoise sea far below", "push_in", "cut"),
    (14, 12, "C", "sunlit yacht salon interior, laptop and coffee cup on a marble table, sea through large windows", "drift", "cut"),
    (15, 12, "Cn", "two silhouettes playing chess on a high night balcony, glowing skyscraper skyline behind, seen from behind", "orbit", "whip"),
    (16, 24, "C", "modern glass house lounge over the ocean at sunset, two silhouettes relaxing on a sofa, warm horizon", "slide_left", "cut"),
    (17, 12, "C", "silver hard-shell suitcase on a palm-lined driveway, man in grey tracksuit walking away seen from behind, white SUV side silhouette, tall palm trees, sunset", "push_in", "cut"),
    (18, 12, "C", "young man seen from behind with arms spread wide in front of a private jet at dusk, golden sky", "pull_out", "cut"),
    (19, 24, "C", "back view of a man on a lounger with arms spread wide, open laptop beside him, calm mountain lake in soft evening light", "drift", "light_leak"),
    (20, 12, "C", "POV laptop on a dark wooden forest terrace railing, blurred stock charts on screen, hand with watch on trackpad, misty hills at sunrise", "push_in", "cut"),
    (21, 12, "C", "extreme close up of a wrist with a gold ring and a watch seen from the side, hand resting on a leather steering wheel, blurred dashboard", "slide_right", "cut"),
    (22, 12, "C", "silhouette of a man in a dark suit sipping coffee by a huge library window at sunset, old-money study, vintage warm film look, skyline", "push_in", "cut"),
    (23, 36, "C", "rooftop terrace overlooking a vast city skyline at golden hour, sweeping cinematic view, lounge chairs", "sweep", "light_leak"),
    (24, 12, "Cn", "hand opening the door of a black luxury car at night, warm interior glow, wet street", "push_in", "whip"),
    (25, 24, "C", "aerial view of a modern glass villa on a cliff over the sea at sunset, infinity pool, tiny distant silhouette", "pull_out", "cut"),
    (26, 36, "C", "young man with dark curly hair seen from behind with a laptop on a cliffside Mediterranean balcony at golden hour, turquoise bay with boats below", "push_in", "light_leak"),
    (27, 60, "D", "balcony table with an espresso, open notebook and closed laptop, silhouette of a young man looking out at the sea, soft golden light", "push_in_slowest", "cut"),
    (28, 60, "D", None, "grid_pullback", "cut"),  # composite of all stills, built locally
]
assert sum(s[1] for s in SHOTS) == 720


def prompt(shot):
    return f"{shot[3]}, {PHASE[shot[2]]}, {COMPACT}"
