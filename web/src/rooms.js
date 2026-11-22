// Everything a visitor reads in the side panel lives here, so the text can be
// edited without touching any of the 3D code.
//
// One entry per stop on the tour, in tour order (Previous / Next follow this list).
//   id     used in the page link, e.g. #dining
//   floor  "out", "g" (ground) or "u" (upstairs): which view the stop belongs to
//   at     where its label floats in the model [x, y, z] in metres
//   view   where the camera flies to: [camera position, point it looks at]
//   links  [label, url, opens another room or the resume?, quieter button style?]
//   todo   a note to self, shown in the panel until the real copy is in
//   near   (optional) lets the camera come closer than usual, for close-ups like
//          the chessboard; the camera then drops in from above instead of flying straight
//   moment (optional) the camera in the manifest this stop is staged for; things
//          modelled to travel with that camera (the visitor's martini) show there
//   click  (optional) materials in the model that open this stop's panel when
//          clicked or tapped, like the contact card on the pool deck's table
//   room   (optional) the furnished room whose furniture this stop shows, when it
//          isn't the stop's own id (the resume stop shows the foyer)
//   hit    (optional) a box in the model, [[x0, y0, z0], [x1, y1, z1]] in metres, that
//          opens `opens` when clicked or tapped, if nothing solid is in front of it
//          (the little door under the stairs, blender/villa/house.py, stairs)
//   opens  (optional, with hit) "resume" opens the resume view; otherwise this stop's panel
//
// A body line is a paragraph, or, if it starts with a block tag ("<ul", "<div", "<p"), placed as it is.

const SPOTIFY = "https://open.spotify.com/user/1d28or5pw94npy3s8ogw5hs3d";

export const ROOMS = [
  {id: "driveway", floor: "out", area: "The driveway", title: "Hi, I'm Aditya", at: [-3, 1.6, 13], view: [[-12, 3.2, 19], [-2.6, 1, 10.6]],
    body: ["Fourth-year Computer Science student at Dalhousie, graduating in 2027. I build software, run a small business, and compete as an amateur in boxing and Muay Thai. Every room in this house is something I’ve built or something I do."],
    links: [["Start the tour", "#dining", 1]]},

  {id: "dining", floor: "g", area: "Dining room", title: "Meruem Chess Coach", at: [-2.3, 1.9, -4.3],
    // the visitor's seat at the table, looking down over the board (blender/villa/dining.py, CHESS_CAM)
    view: [[-1.23, 1.30, -3.52], [-1.25, 0.77, -4.35]], near: 0.4,
    body: ["I started learning chess and wanted a coach that goes into the why: why one move is best, how to calculate a line, how to approach a position. So I built one. I used Stockfish to grade and compute moves, Maia to emulate a real opponent at any elo, and Claude for explanation and reasoning behind engine lines. It is serverless and adaptive in difficulty.",
      "On the table: a Ruy Lopez, Chigorin variation, after 16...Bd7."],
    links: [["Live site", "https://zvezda4994.github.io/Meruem-Chess-Coach/"], ["Code", "https://github.com/Zvezda4994/Meruem-Chess-Coach", 0, 1]]},

  {id: "study", floor: "g", area: "The study", title: "VAREK Systems", at: [3.75, 1.7, 4],
    // from behind the sofa, looking over it at the whiteboard (blender/villa/study.py, STUDY_CAM)
    view: [[5.8, 1.55, 2.95], [1.5, 1.05, 1.75]], near: 0.4,
    body: ["VAREK Systems is an AI automation agency I co-founded with Matthew. The first product is an AI receptionist for local Halifax businesses: it picks up the calls that would otherwise go to voicemail and books the appointment. Built on Synthflow. It’s early; no clients yet."]},

  {id: "garage", floor: "g", area: "The garage", title: "Turo", at: [-8.5, 1.7, 4],
    // inside the garage door, between the bays, looking at the keys and the screen (blender/villa/garage.py, GARAGE_CAM)
    view: [[-8.15, 1.6, 7.2], [-8.7, 1.12, 0]], near: 0.4,
    body: ["I run a four-car rental fleet on Turo: 150+ five-star reviews, a 5.0 average, and All-Star Host three years running. It’s been a real education in pricing, customer service and logistics."]},

  {id: "gym", floor: "g", area: "Home gym", title: "Combat sports", at: [9, 1.7, 4],
    // behind the heavy bag, looking at the gear wall (blender/villa/gym.py, GYM_CAM)
    view: [[8.75, 1.4, 6.3], [7.15, 1.0, 0.25]], near: 0.4,
    body: ["I’ve trained and competed in combat sports since I was 14, mostly Muay Thai, kickboxing and boxing, at Grant’s Martial Arts in Dartmouth."]},

  {id: "living", floor: "g", area: "Living room", title: "The fish tank", at: [6.5, 1.9, -6.6],
    // by the study door, across the sofa to the tank, the moodboard on the right (blender/villa/living.py, LIVING_CAM).
    // The moodboard's frames get a fresh random pick from web/assets/moodboard/ each time the room opens.
    view: [[3.45, 1.45, -0.8], [9.4, 1.05, -6.2]], near: 0.4,
    body: ["I started learning Blender only for this project, and ended up quite liking the process and intricacies of 3D modeling. This tank is my favourite."]},

  {id: "kitchen", floor: "g", area: "Kitchen", title: "Tools and stack", at: [-8.5, 1.7, -4],
    // sitting at the island, looking across it at the labelled shelves (blender/villa/kitchen.py, KITCHEN_CAM)
    view: [[-6.45, 1.36, -3.02], [-6.62, 1.47, -0.075]], near: 0.4,
    body: ["<b>Languages:</b> Python, Java, JavaScript, SQL, C, HTML/CSS.",
      "<b>Frameworks and libraries:</b> React, Node.js, Flask, Streamlit, pandas, NumPy, scikit-learn, PyTorch, three.js.",
      "<b>Tools:</b> Git, Google Cloud, Apps Script, SQLite, BeautifulSoup, Blender, Stockfish, ONNX Runtime."]},

  {id: "stairs", floor: "g", area: "Under the stairs", title: "Resume", at: [-2.4, 1.5, 1.6], room: "foyer",
    // in the foyer's front corner, across to the stairs, the plinth and the resume door (blender/villa/foyer.py, FOYER_CAM)
    view: [[0.4, 1.6, 7.0], [-2.6, 1.0, 1.0]], near: 0.4,
    hit: [[-2.79, 0.0, 1.37], [-1.96, 1.34, 1.47]], opens: "resume",
    body: ["My resume as a plain page, for anyone short on time."],
    links: [["Open resume", "#resume", 1]]},

  {id: "library", floor: "u", area: "Library", title: "Books and writing", at: [6.75, 5.2, 4],
    // from the landing door, across to the east wall's shelves, the desk on the right (blender/villa/library.py, LIBRARY_CAM)
    view: [[2.55, 5.0, 5.75], [11.0, 4.7, 3.05]], near: 0.4,
    body: ["Reading has been a formative habit for as long as I can remember. I greatly enjoy literature of intrigue like Dumas, Fleming, and old Travis McGee mysteries, as well as getting insights into high performers and frameworks that promote novel ways of thinking. Ask me about the one I’m writing!"]},

  {id: "trophy", floor: "u", area: "Trophy room", title: "Wins", at: [8, 5.2, -4],
    // inside the games room door, looking at the display wall, the terrace on the left (blender/villa/trophy.py, TROPHY_CAM)
    view: [[4.6, 5.05, -3], [11.7, 4.7, -4.6]], near: 0.4,
    // two prominent groups, then the small print (styles.css, .wins and .fine)
    body: ["<div class='wins'><section><h3>Boxing</h3><ul><li>SGFI Youth, gold.</li><li>SAF Junior National Capital Championship, silver.</li></ul></section>" +
        "<section><h3>Esports</h3><ul><li>7th at TomorrowLAN 2026 with Dalhousie Gold.</li><li>CCL playoffs, Spring 2026.</li></ul></section></div>",
      "<p class='fine'>Sexton Scholar and Dean’s List at Dalhousie. In high school: Sarthak IT Fest winner, and a member of the student cabinet.</p>"]},

  {id: "games", floor: "u", area: "Games room", title: "CS2 and CounterPick", at: [-0.5, 5.2, -4],
    // behind the chair, looking at the screens, the PC on the floor at the left: games.py's DESK_CAM
    // ("games_desk"), drawn back along its line to frame the same at the site's 45° (it's 55°)
    view: [[-1.27, 5.04, -2.35], [-4.725, 4.6, -4.3]], near: 0.4,
    body: ["CounterPick is a Pick’Em optimizer for CS2 Majors. It turns betting odds into team strengths with a Bradley-Terry fit, simulates each Swiss stage 100,000 times under Valve’s rulebook (about a second in NumPy), and searches all 10 million legal cards for the one most likely to get at least 5 of 10 right. The simulator reproduces every pairing of the Austin 2025 Major. Built for the PGL Singapore Major; results go up as the event runs.",
      "I also play on Dalhousie Gold. We finished 7th at TomorrowLAN 2026 and made the CCL playoffs in Spring 2026."],
    links: [["github.com/Zvezda4994/CounterPick", "https://github.com/Zvezda4994/CounterPick"], ["TomorrowLAN", "https://www.instagram.com/p/DVyjCCAjaVB/", 0, 1]]},

  {id: "bedroom", floor: "u", area: "Main bedroom", title: "Languages and music", at: [-8.5, 5.2, -3],
    // from the corner by the glass, across the bed to the headboard, the map on the right (blender/villa/bedroom.py, BEDROOM_CAM)
    view: [[-10.55, 5.05, -6.55], [-5.6, 4.45, -1.2]], near: 0.4,
    body: ["<b>French:</b> C1. <b>Russian:</b> B1. <b>Japanese:</b> A2.",
      "The easiest way into a language is usually its music and films."],
    links: [["Spotify", SPOTIFY]]},

  {id: "pool", floor: "out", area: "Pool deck", title: "Get in touch", at: [-0.3, 2.1, -17.4],
    // the visitor's lounger, looking out over the pool to the house (blender/villa/pool.py, MOMENT_CAM)
    view: [[-1.351, 0.98, -18.062], [0.35, 0.56, -15.63]], near: 0.3, moment: "pool_moment",
    click: ["card", "card_back"],
    body: ["Open to internships and software roles. Email is the fastest way to reach me.",
      "<a href='mailto:adityaviveksingh@icloud.com'>adityaviveksingh@icloud.com</a><br><a href='https://www.linkedin.com/in/aditya-singh' target='_blank' rel='noopener'>linkedin.com/in/aditya-singh</a><br><a href='https://github.com/Zvezda4994' target='_blank' rel='noopener'>github.com/Zvezda4994</a>"]},
];

// Hotspots: small pulsing dots on things in a room, shown only while the camera is inside
// that stop's room (never in the overviews). Each sits on an anchor exported with its room
// (blender/villa/geo.py, Builder.anchor; manifest.hotspots) and does one thing:
//   view    flies the camera there: [camera position, point it looks at]
//   resume  opens the resume view
//   url     opens a page in a new tab
//   tip     shows a small note beside the dot, with no camera move
// `label` is for screen readers and the mouse's tooltip; the dot itself shows no text.
export const HOTSPOTS = [
  // sat on the sofa's middle seat, eyes about 0.7 m over the cushion, facing the TV (living.py, TV_X)
  {anchor: "living_couch_seat", stop: "living", label: "Sit on the sofa", view: [[6.4, 1.12, -4.1], [6.3, 1.0, -0.1]]},
  {anchor: "resume_door", stop: "stairs", label: "Open the resume", resume: true},
  // the east wall's eye-level shelves, bays 3 and 4, where the real titles stand (library.py, SPINES_CAM)
  {anchor: "library_real_books", stop: "library", label: "Look at the books", view: [[9.95, 4.98, 4.07], [11.34, 4.93, 4.07]]},
  {anchor: "bedroom_record_player", stop: "bedroom", label: "Open my Spotify", url: SPOTIFY},
  {anchor: "gym_gloves", stop: "gym", label: "The brown gloves", tip: "A gift from a mentor."},
];

export const FLOOR_NAME = {out: "Outside", g: "Ground floor", u: "Upstairs"};

// Where a visitor is likely to go from each stop: the next stop on the tour first, then
// the rooms through its doors. While a stop is open these load ahead of the rest. A name
// that isn't a stop is a furnished part of the house with no stop of its own (the
// upstairs landing, blender/villa/landing.py).
export const NEIGHBOURS = {
  driveway: ["dining", "stairs", "garage", "study"],
  dining: ["study", "kitchen", "living", "stairs", "pool"],
  study: ["garage", "gym", "living", "stairs"],
  garage: ["gym", "kitchen", "stairs"],
  gym: ["living", "study"],
  living: ["kitchen", "gym", "study", "dining", "pool"],
  kitchen: ["stairs", "dining", "garage"],
  stairs: ["library", "landing", "dining", "games", "garage"],
  library: ["trophy", "landing", "games", "stairs"],
  trophy: ["games", "library", "landing", "pool"],
  games: ["bedroom", "landing", "trophy", "library"],
  bedroom: ["pool", "games", "landing", "library"],
  pool: ["driveway", "living", "dining", "trophy"],
};

// The resume itself is web/resume.json (drawn by src/resume.js).
