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
//
// The copy is still draft. Rooms marked todo are waiting on real numbers and lists.

export const ROOMS = [
  {id: "driveway", floor: "out", area: "The driveway", title: "Hi, I'm Aditya", at: [-3, 1.6, 13], view: [[-12, 3.2, 19], [-2.6, 1, 10.6]],
    body: ["Fourth-year Computer Science co-op student at Dalhousie University, graduating in 2027.",
      "I build software, run two small businesses and coach boxing. Every room in this house is something I've built or something I do. Use the labels, or the Rooms menu."],
    links: [["Start the tour", "#dining", 1]]},

  {id: "dining", floor: "g", area: "Dining room", title: "Meruem Chess Coach", at: [-2.3, 1.9, -4.3],
    // the visitor's seat at the table, looking down over the board (blender/villa/dining.py, CHESS_CAM)
    view: [[-1.23, 1.30, -3.52], [-1.25, 0.77, -4.35]], near: 0.4,
    body: ["A chess trainer that explains every move. Stockfish runs the analysis, Maia (a neural net trained on human games) plays like a real opponent at my rating, and Claude writes the explanations using the engine's lines.",
      "Static site, no backend. Everything runs in the browser in Web Workers.",
      "On the table: a Ruy Lopez, Chigorin variation, after 16...Bd7. White to move, and it's your seat."],
    links: [["Live site", "https://zvezda4994.github.io/Meruem-Chess-Coach/"], ["Code", "https://github.com/Zvezda4994/Meruem-Chess-Coach", 0, 1]]},

  {id: "study", floor: "g", area: "The study", title: "VAREK Systems", at: [3.75, 1.7, 4],
    // from behind the sofa, looking over it at the whiteboard (blender/villa/study.py, STUDY_CAM)
    view: [[5.8, 1.55, 2.95], [1.5, 1.05, 1.75]], near: 0.4,
    body: ["Co-founder of an AI automation agency for local Halifax businesses: voice agents and workflow automation built on Synthflow."],
    todo: "Add two client case studies with one number each (calls handled, hours saved)."},

  {id: "garage", floor: "g", area: "The garage", title: "Turo fleet", at: [-8.5, 1.7, 4],
    // inside the garage door, between the bays, looking at the keys and the screen (blender/villa/garage.py, GARAGE_CAM)
    view: [[-8.15, 1.6, 7.2], [-8.7, 1.12, 0]], near: 0.4,
    body: ["I run a four-car rental fleet on Turo with my dad: pricing, scheduling, guest communication and maintenance."],
    todo: "Add utilisation or revenue figures, and any tooling you built for it."},

  {id: "gym", floor: "g", area: "Home gym", title: "Boxing", at: [9, 1.7, 4],
    // behind the heavy bag, looking at the gear wall (blender/villa/gym.py, GYM_CAM)
    view: [[8.75, 1.4, 6.3], [7.15, 1.0, 0.25]], near: 0.4,
    body: ["Competitive boxer for years, and now a coach to more than 30 athletes."],
    todo: "A photo and one line on your coaching approach would land well here."},

  {id: "living", floor: "g", area: "Living room", title: "The fish tank", at: [6.5, 1.9, -6.6],
    // by the study door, across the sofa to the tank, the moodboard on the right (blender/villa/living.py, LIVING_CAM).
    // The moodboard's frames get a fresh random pick from web/assets/moodboard/ each time the room opens.
    view: [[3.45, 1.45, -0.8], [9.4, 1.05, -6.2]], near: 0.4,
    body: ["Floor-to-ceiling tank with a moss-covered mech resting on the bottom. Pure decoration, and the thing guests ask about first."],
    todo: "The tank and the mech arrive when this room is furnished."},

  {id: "kitchen", floor: "g", area: "Kitchen", title: "Tools and stack", at: [-8.5, 1.7, -4],
    // sitting at the island, looking across it at the labelled shelves (blender/villa/kitchen.py, KITCHEN_CAM)
    view: [[-6.45, 1.36, -3.02], [-6.62, 1.47, -0.075]], near: 0.4,
    body: ["What I build with day to day."],
    todo: "List languages, frameworks and tools you can defend in an interview."},

  {id: "stairs", floor: "g", area: "Under the stairs", title: "Resume", at: [-2.4, 1.5, 1.6], room: "foyer",
    // in the foyer's front corner, across to the stairs, the plinth and the resume door (blender/villa/foyer.py, FOYER_CAM)
    view: [[0.4, 1.6, 7.0], [-2.6, 1.0, 1.0]], near: 0.4,
    body: ["The full resume as a plain page, for anyone short on time."],
    links: [["Open resume", "#resume", 1]]},

  {id: "library", floor: "u", area: "Library", title: "Books and writing", at: [6.75, 5.2, 4],
    // from the landing door, across to the east wall's shelves, the desk on the right (blender/villa/library.py, LIBRARY_CAM)
    view: [[2.55, 5.0, 5.75], [11.0, 4.7, 3.05]], near: 0.4,
    body: ["The books I rate, and my own writing. I'm working on a book; excerpts and notes will live here."],
    todo: "Add the reading list, and a short excerpt once you're happy to share one."},

  {id: "trophy", floor: "u", area: "Trophy room", title: "Wins", at: [8, 5.2, -4],
    // inside the games room door, looking at the display wall, the terrace on the left (blender/villa/trophy.py, TROPHY_CAM)
    view: [[4.6, 5.05, -3], [11.7, 4.7, -4.6]], near: 0.4,
    body: ["Wins in coding, boxing and esports."],
    todo: "Add the trophy list: what, when, and one line on each."},

  {id: "games", floor: "u", area: "Games room", title: "CS2 and the pick'em model", at: [-0.5, 5.2, -4],
    // from beside the sofa, across the room to the setup (blender/villa/games.py, GAMES_CAM)
    view: [[1.625, 5.12, -2.1], [-4.325, 4.42, -4.65]], near: 0.4,
    body: ["I compete on Dalhousie's collegiate esports team in Counter-Strike 2, and built a win-probability model for pick'em predictions."],
    todo: "Link the model's repo and give its accuracy against a baseline."},

  {id: "bedroom", floor: "u", area: "Main bedroom", title: "Languages", at: [-8.5, 5.2, -3],
    // from the corner by the glass, across the bed to the headboard, the map on the right (blender/villa/bedroom.py, BEDROOM_CAM)
    view: [[-10.55, 5.05, -6.55], [-5.6, 4.45, -1.2]], near: 0.4,
    body: ["Currently learning Darija, Russian and Japanese."],
    todo: "Optional. Keep it if you can hold a short conversation in at least one."},

  {id: "pool", floor: "out", area: "Pool deck", title: "Get in touch", at: [-0.3, 2.1, -17.4],
    // the visitor's lounger, looking out over the pool to the house (blender/villa/pool.py, MOMENT_CAM)
    view: [[-1.351, 0.98, -18.062], [0.35, 0.56, -15.63]], near: 0.3, moment: "pool_moment",
    click: ["card", "card_back"],
    body: ["Open to co-op and new-grad roles for 2027.",
      "Pull up a lounger. My details are on the card on the table."],
    links: [["GitHub", "https://github.com/Zvezda4994"]],
    todo: "Add your email and LinkedIn as plain text. The card on the table shows placeholders until then (CONTACT_CARD in blender/villa/config.py)."},
];

export const FLOOR_NAME = {out: "Outside", g: "Ground floor", u: "Upstairs"};

// The plain resume page behind "Skip to resume". Each section is [heading, [[title, detail], ...]].
export const RESUME = {
  name: "Aditya",
  sections: [
    ["Education", [["Dalhousie University, BCS (Co-op)", "Halifax, NS · expected 2027"]]],
    ["Projects", [
      ["Meruem Chess Coach", "Chess trainer running Stockfish, the Maia neural net and an LLM coach entirely in the browser. <a href='https://zvezda4994.github.io/Meruem-Chess-Coach/' target='_blank' rel='noopener'>Live</a> · <a href='https://github.com/Zvezda4994/Meruem-Chess-Coach' target='_blank' rel='noopener'>Code</a>"],
      ["CS2 pick'em model", "Win-probability model for Counter-Strike 2 match predictions."]]],
    ["Work", [["VAREK Systems, co-founder", "AI automation agency for local businesses."], ["Turo fleet", "Operations for a four-car rental fleet."]]],
    ["Also", [["Boxing", "Competitive boxer; coach to 30+ athletes."], ["Esports", "Dalhousie collegiate CS2 team."]]],
  ],
  todo: "Draft from what I know about you. Swap in your real resume content.",
};
