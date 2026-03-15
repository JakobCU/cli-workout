export interface ExerciseVariant {
  name: string;
  slug: string;
  description: string;
  muscle_groups: string[];
  default_value: number;
}

export interface Exercise {
  name: string;
  slug: string;
  description: string;
  muscle_groups: string[];
  default_mode: "time" | "reps";
  default_value: number;
  tips: string[];
  variants: ExerciseVariant[];
  animation_frames: string[];
}

export const EXERCISES: Exercise[] = [
  {
    name: "Push-Ups",
    slug: "push-ups",
    description: "The king of bodyweight exercises. Targets chest, shoulders, and triceps through a full push-pull motion from the floor.",
    muscle_groups: ["chest", "shoulders", "triceps"],
    default_mode: "time",
    default_value: 30,
    tips: [
      "Keep your core tight and body in a straight line",
      "Lower until chest nearly touches the floor",
      "Push through your palms, not your fingers",
    ],
    variants: [
      { name: "Wide Push-Ups", slug: "wide-push-ups", description: "Wider hand placement shifts emphasis to the outer chest and shoulders.", muscle_groups: ["chest", "shoulders"], default_value: 25 },
      { name: "Diamond Push-Ups", slug: "diamond-push-ups", description: "Hands close together forming a diamond shape. Heavy triceps emphasis.", muscle_groups: ["triceps", "chest", "shoulders"], default_value: 20 },
      { name: "Incline Push-Ups", slug: "incline-push-ups", description: "Hands elevated on a surface. Easier variation, good for beginners.", muscle_groups: ["chest", "shoulders", "triceps"], default_value: 30 },
      { name: "Decline Push-Ups", slug: "decline-push-ups", description: "Feet elevated on a surface. Increases upper chest and shoulder activation.", muscle_groups: ["chest", "shoulders", "triceps"], default_value: 25 },
    ],
    animation_frames: [
`           \\  /
        .-''''-.          *
       / @    @ \\        /
      |  (~~~~)  |      /
       \\ \`----' /    __/
    ----\`------'----'
   /  /            \\  \\
  +--+              +--+
 _|  |______________|  |_
/////              \\\\\\\\\\`,
`           \\  /
        .-''''-.         .
       / @    @ \\       /
      |  (~~~~)  |    _/
       \\ \`----' /  __/
    ----\`------'-''
   / /              \\ \\
  +'+    ________    '+'
 _|  |__|        |__|  |_
/////              \\\\\\\\\\`,
`           \\  /
        .-''''-.        '
       / >    < \\      /
      |  (~~~~)  |   _/
       \\ \`----' /__-'
    ----\`------''
   //                \\\\
  +'  ________________ '+
 _|__|                |__|
/////              \\\\\\\\\\`,
`          \\  /     *
        .-''''-.
       / ^    ^ \\    *
      |  (~~~~)  |      *
       \\ \`----' /    __/
    ----\`------'----'
   /  /            \\  \\
  +--+              +--+
 _|  |______________|  |_
/////              \\\\\\\\\\`,
    ],
  },
  {
    name: "Squats",
    slug: "squats",
    description: "Fundamental lower body compound movement. Builds quad, glute, and hamstring strength through a deep knee bend.",
    muscle_groups: ["quads", "glutes", "hamstrings"],
    default_mode: "time",
    default_value: 40,
    tips: [
      "Keep weight in your heels, not your toes",
      "Push knees out over your toes, don't let them cave in",
      "Go as deep as your mobility allows",
    ],
    variants: [
      { name: "Jump Squats", slug: "jump-squats", description: "Explosive squat with a jump at the top. Builds power and burns calories fast.", muscle_groups: ["quads", "glutes", "calves"], default_value: 20 },
      { name: "Sumo Squats", slug: "sumo-squats", description: "Wide stance with toes pointed out. Emphasizes inner thighs and glutes.", muscle_groups: ["quads", "glutes", "adductors"], default_value: 35 },
      { name: "Wall Sit", slug: "wall-sit", description: "Isometric hold with back against a wall at 90 degrees. Pure quad endurance.", muscle_groups: ["quads", "glutes"], default_value: 30 },
    ],
    animation_frames: [
`            \\  /
         .-''''-.
        / @    @ \\
       |  (~~~~)  |
        \\ \`----' /
         '------'
            ||
           /  \\
          /    \\
         |      |
        _|_    _|_`,
`            \\  /
         .-''''-.
        / o    o \\    '
       |  (~~~~)  |
        \\ \`----' /
         '------'
        /  /  \\  \\
       / _/    \\_ \\
      | /        \\ |
      |/          \\|`,
`            \\  /      ~
         .-''''-.     o
        / >    < \\
       |  (~~~~)  |
        \\ \`----' /
       /-'------'-\\
      / /  ____  \\ \\
     / / /    \\ \\ \\ \\
    |  |/      \\|  |
    |__|        |__|`,
`            \\  /      *
         .-''''-.
        / ^    ^ \\
       |  (~~~~)  |
        \\ \`----' /
         '------'
            ||
           /  \\
          /    \\
         |      |
        _|_    _|_`,
    ],
  },
  {
    name: "Plank",
    slug: "plank",
    description: "Isometric core hold that builds total-body stability. The foundation of core training.",
    muscle_groups: ["core", "shoulders"],
    default_mode: "time",
    default_value: 30,
    tips: [
      "Squeeze your glutes and brace your abs",
      "Keep a neutral spine -- don't let hips sag or pike up",
      "Breathe steadily, don't hold your breath",
    ],
    variants: [
      { name: "Plank Shoulder Taps", slug: "plank-shoulder-taps", description: "Alternate tapping opposite shoulder while holding plank. Anti-rotation challenge.", muscle_groups: ["core", "shoulders", "obliques"], default_value: 25 },
      { name: "Forearm Plank", slug: "forearm-plank", description: "Resting on forearms instead of hands. More core, less wrist strain.", muscle_groups: ["core", "shoulders"], default_value: 35 },
    ],
    animation_frames: [
`        \\  /
     .-''''-.___________________________________
    / @    @ \\__________________________________\\
   |  (~~~~)  |                                  |
    \\ \`----' /                                   |
     \`------+-----------------------------------'
    /  /     \\                              \\
   +--+      +------------------------------+
  (===)                                (===)`,
`        \\  /
     .-''''-.___________________________________
    / @    @ \\__________________________________\\
   |  (~~~~)  |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~|
    \\ \`----' /                                   |
     \`------+-----------------------------------'
    / /       \\                              \\
   +'+        +------------------------------+
  (===)                                (===)`,
`        \\  /                              ~
     .-''''-.___________________________________
    / -    - \\__________________________________\\
   |  (~~~~)  |                                  |
    \\ \`----' /  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ |
     \`------+-----------------------------------'
    /  /     \\                              \\
   +--+      +------------------------------+
  (===)                                (===)`,
    ],
  },
  {
    name: "Reverse Lunges",
    slug: "reverse-lunges",
    description: "Step back into a deep lunge, alternating legs. Easier on the knees than forward lunges while building unilateral leg strength.",
    muscle_groups: ["quads", "glutes", "hamstrings"],
    default_mode: "time",
    default_value: 35,
    tips: [
      "Step back far enough that both knees hit 90 degrees",
      "Keep your torso upright, don't lean forward",
      "Push off your front heel to return to standing",
    ],
    variants: [
      { name: "Walking Lunges", slug: "walking-lunges", description: "Continuous forward-stepping lunges. Requires space but great for coordination.", muscle_groups: ["quads", "glutes", "hamstrings"], default_value: 30 },
      { name: "Curtsy Lunges", slug: "curtsy-lunges", description: "Step diagonally behind your front leg. Extra emphasis on glute medius.", muscle_groups: ["glutes", "quads", "adductors"], default_value: 30 },
    ],
    animation_frames: [
`            \\  /
         .-''''-.
        / @    @ \\
       |  (~~~~)  |
        \\ \`----' /
         '------'
            ||
           /  \\
          /    \\
         |      |
        _|_    _|_`,
`            \\  /
         .-''''-.
        / @    @ \\
       |  (~~~~)  |
        \\ \`----' /
         '------'
          / |
         /  |
        |   |  \\
        |_  |   \\
            |    \\__`,
`            \\  /       ~
         .-''''-.      o
        / >    < \\
       |  (~~~~)  |
        \\ \`----' /
         '------'
          / |
         /  |
        |   |   \\
        |   |    \\
        |_  |     \\___`,
`            \\  /       *
         .-''''-.
        / ^    ^ \\
       |  (~~~~)  |
        \\ \`----' /
         '------'
            ||
           /  \\
          /    \\
         |      |
        _|_    _|_`,
    ],
  },
  {
    name: "Superman",
    slug: "superman",
    description: "Lie face down and lift arms and legs off the floor. Strengthens the entire posterior chain, especially lower back.",
    muscle_groups: ["lower back", "glutes"],
    default_mode: "time",
    default_value: 25,
    tips: [
      "Lift arms and legs simultaneously",
      "Squeeze your glutes at the top",
      "Keep your neck neutral -- look at the floor, not forward",
    ],
    variants: [
      { name: "Swimming Superman", slug: "swimming-superman", description: "Alternate lifting opposite arm and leg in a flutter motion. More dynamic.", muscle_groups: ["lower back", "glutes", "shoulders"], default_value: 25 },
      { name: "Superman Hold", slug: "superman-hold", description: "Static hold at the top position. Pure isometric back endurance.", muscle_groups: ["lower back", "glutes"], default_value: 20 },
    ],
    animation_frames: [
`                                *  *
        \\  /                  *
     .-''''-._____________  *
    / ^    ^ \\_____________>
   |  (~~~~)  |============/
    \\ \`----' /
     \`------'
    /  /  \\  \\
   +--+    +--+`,
`                               *    *
        \\  /                 *
     .-''''-.______________*
    / @    @ \\______________>
   |  (~~~~)  |=============/
    \\ \`----' /
     \`------'
    /  /  \\  \\
   +--+    +--+`,
`                              *      *
        \\  /                *
     .-''''-._____________ *
    / ^    ^ \\______________>
   |  (~~~~)  |============/
    \\ \`----' /
     \`------'
    / /    \\ \\
   +'+      +'+`,
    ],
  },
  {
    name: "Side Plank Left",
    slug: "side-plank-left",
    description: "Lateral isometric hold on the left side. Targets obliques and builds anti-lateral-flexion stability.",
    muscle_groups: ["obliques", "core"],
    default_mode: "time",
    default_value: 20,
    tips: [
      "Stack your feet or stagger them for more stability",
      "Keep your hips elevated -- don't let them sag",
      "Free arm can reach to the ceiling for extra challenge",
    ],
    variants: [
      { name: "Side Plank Left Dips", slug: "side-plank-left-dips", description: "Lower and raise hips while in side plank. Dynamic oblique work.", muscle_groups: ["obliques", "core"], default_value: 20 },
    ],
    animation_frames: [
`         \\  /
      .-''''-.
     / @    @ \\
    |  (~~~~)  |
     \\  \`--'  /=========================
      \`------'
      /  |
     /   |
    +----+`,
`         \\  /                        ~
      .-''''-.
     / @    @ \\
    |  (~~~~)  |
     \\  \`--'  /==========================
      \`------'
     /   |
     /   |
    +----+`,
`         \\  /                    ~   o
      .-''''-.
     / o    o \\
    |  (~~~~)  |
     \\  \`--'  /=========================
      \`------'
      /  |
     /   |
    +----+`,
    ],
  },
  {
    name: "Side Plank Right",
    slug: "side-plank-right",
    description: "Lateral isometric hold on the right side. Targets obliques and builds anti-lateral-flexion stability.",
    muscle_groups: ["obliques", "core"],
    default_mode: "time",
    default_value: 20,
    tips: [
      "Stack your feet or stagger them for more stability",
      "Keep your hips elevated -- don't let them sag",
      "Free arm can reach to the ceiling for extra challenge",
    ],
    variants: [
      { name: "Side Plank Right Dips", slug: "side-plank-right-dips", description: "Lower and raise hips while in side plank. Dynamic oblique work.", muscle_groups: ["obliques", "core"], default_value: 20 },
    ],
    animation_frames: [
`                                 \\  /
                              .-''''-.
                             / @    @ \\
                            |  (~~~~)  |
     ========================\\  \`--'  /
                              \`------'
                                  |  \\
                                  |   \\
                                  +----+`,
`  ~                              \\  /
                              .-''''-.
                             / @    @ \\
                            |  (~~~~)  |
     =========================\\  \`--'  /
                              \`------'
                                  |   \\
                                  |   \\
                                  +----+`,
`  ~  o                           \\  /
                              .-''''-.
                             / o    o \\
                            |  (~~~~)  |
     ========================\\  \`--'  /
                              \`------'
                                  |  \\
                                  |   \\
                                  +----+`,
    ],
  },
  {
    name: "Glute Bridge",
    slug: "glute-bridge",
    description: "Lying hip thrust that isolates the glutes and hamstrings. Essential for posterior chain activation.",
    muscle_groups: ["glutes", "hamstrings"],
    default_mode: "time",
    default_value: 35,
    tips: [
      "Drive through your heels, not your toes",
      "Squeeze your glutes hard at the top",
      "Keep your ribs down -- don't hyperextend your lower back",
    ],
    variants: [
      { name: "Single-Leg Glute Bridge", slug: "single-leg-glute-bridge", description: "One leg elevated. Doubles the load on the working glute. Great for fixing imbalances.", muscle_groups: ["glutes", "hamstrings"], default_value: 25 },
      { name: "Marching Glute Bridge", slug: "marching-glute-bridge", description: "Alternate lifting knees while holding the bridge position. Core and glute challenge.", muscle_groups: ["glutes", "hamstrings", "core"], default_value: 30 },
    ],
    animation_frames: [
`        \\  /
     .-''''-.
    / @    @ \\  __
   |  (~~~~)  |/  \\___
    \\ \`----' /      __\\___
     \`------+------'      \\
    /  /     \\             |
   +--+       +===========+`,
`        \\  /
     .-''''-.  _
    / @    @ \\/  \\___
   |  (~~~~) /      _\\___
    \\ \`----'/            \\
     \`-----+-------.     |
    /  /    \\        \\    |
   +--+      +========+==+`,
`        \\  /
     .-''''-.____
    / ^    ^ \\   \\___
   |  (~~~~)  |     _\\___
    \\ \`----' /           \\
     \`------+-------.     |
    / /      \\       \\    |
   +'+        +======+===+`,
    ],
  },
  {
    name: "Bird Dog",
    slug: "bird-dog",
    description: "From all fours, extend opposite arm and leg. Builds core stability and coordination while strengthening the posterior chain.",
    muscle_groups: ["core", "lower back"],
    default_mode: "time",
    default_value: 30,
    tips: [
      "Move slowly and with control",
      "Keep your hips square to the ground -- don't rotate",
      "Reach long through your fingers and toes",
    ],
    variants: [
      { name: "Dead Bug", slug: "dead-bug", description: "The inverse of bird dog -- lying face up, extend opposite arm and leg. Core stability without back loading.", muscle_groups: ["core", "hip flexors"], default_value: 30 },
      { name: "Bird Dog Crunch", slug: "bird-dog-crunch", description: "Bring elbow and knee together under your body between extensions. Adds a crunch component.", muscle_groups: ["core", "lower back", "obliques"], default_value: 25 },
    ],
    animation_frames: [
`        \\  /
     .-''''-.________________________
    / @    @ \\_______________________>
   |  (~~~~)  |=====================/
    \\ \`----' /
     \`------'
    /  |  \\
   +---+   +---+`,
`        \\  /
     .-''''-._________________________
    / @    @ \\________________________>
   |  (~~~~)  |======================/
    \\ \`----' /
     \`------'
    / |    \\
   +--+     +---+`,
`        \\  /                          ~
     .-''''-._________________________
    / o    o \\_________________________>
   |  (~~~~)  |=======================/
    \\ \`----' /
     \`------'
    /  |  \\
   +---+   +---+`,
    ],
  },
];

export function getExerciseBySlug(slug: string): Exercise | undefined {
  return EXERCISES.find((e) => e.slug === slug);
}
