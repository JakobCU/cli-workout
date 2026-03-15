export interface Exercise {
  name: string;
  mode: "time" | "reps";
  value: number;
  muscle_groups: string[];
}

export interface OpenWorkout {
  id: string;
  name: string;
  description: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  tags: string[];
  equipment: string[];
  rounds: number;
  estimated_duration_min: number;
  muscle_groups: string[];
  exercises: Exercise[];
  fork_count: number;
}

export const WORKOUTS: OpenWorkout[] = [
  {
    id: "fithub/upper-body",
    name: "Upper Body",
    description: "Push-focused upper body session targeting chest, shoulders, and core.",
    difficulty: "intermediate",
    tags: ["upper-body", "push", "bodyweight"],
    equipment: ["none"],
    rounds: 3,
    estimated_duration_min: 13,
    fork_count: 6,
    muscle_groups: ["chest", "shoulders", "triceps", "core", "lower back"],
    exercises: [
      { name: "Push-Ups", mode: "time", value: 30, muscle_groups: ["chest", "shoulders", "triceps"] },
      { name: "Plank", mode: "time", value: 30, muscle_groups: ["core", "shoulders"] },
      { name: "Superman", mode: "time", value: 25, muscle_groups: ["lower back", "glutes"] },
      { name: "Bird Dog", mode: "time", value: 30, muscle_groups: ["core", "lower back"] },
      { name: "Push-Ups", mode: "time", value: 25, muscle_groups: ["chest", "shoulders", "triceps"] },
    ],
  },
  {
    id: "fithub/lower-body",
    name: "Lower Body",
    description: "Legs and glutes workout with squats and lunges.",
    difficulty: "intermediate",
    tags: ["lower-body", "legs", "bodyweight"],
    equipment: ["none"],
    rounds: 3,
    estimated_duration_min: 14,
    fork_count: 5,
    muscle_groups: ["quads", "glutes", "hamstrings"],
    exercises: [
      { name: "Squats", mode: "time", value: 40, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Reverse Lunges", mode: "time", value: 35, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Glute Bridge", mode: "time", value: 35, muscle_groups: ["glutes", "hamstrings"] },
      { name: "Squats", mode: "time", value: 35, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Reverse Lunges", mode: "time", value: 30, muscle_groups: ["quads", "glutes", "hamstrings"] },
    ],
  },
  {
    id: "fithub/core-blast",
    name: "Core Blast",
    description: "Intense core workout hitting abs, obliques, and lower back.",
    difficulty: "intermediate",
    tags: ["core", "abs", "bodyweight"],
    equipment: ["none"],
    rounds: 3,
    estimated_duration_min: 13,
    fork_count: 8,
    muscle_groups: ["core", "obliques", "lower back", "shoulders", "glutes"],
    exercises: [
      { name: "Plank", mode: "time", value: 35, muscle_groups: ["core", "shoulders"] },
      { name: "Side Plank Left", mode: "time", value: 25, muscle_groups: ["core", "obliques"] },
      { name: "Side Plank Right", mode: "time", value: 25, muscle_groups: ["core", "obliques"] },
      { name: "Superman", mode: "time", value: 30, muscle_groups: ["lower back", "glutes"] },
      { name: "Bird Dog", mode: "time", value: 30, muscle_groups: ["core", "lower back"] },
    ],
  },
  {
    id: "fithub/full-body-easy",
    name: "Full Body Easy",
    description: "Gentle full body session, great for beginners or recovery days.",
    difficulty: "beginner",
    tags: ["full-body", "beginner", "bodyweight"],
    equipment: ["none"],
    rounds: 2,
    estimated_duration_min: 6,
    fork_count: 4,
    muscle_groups: ["chest", "shoulders", "triceps", "quads", "glutes", "hamstrings", "core"],
    exercises: [
      { name: "Push-Ups", mode: "time", value: 20, muscle_groups: ["chest", "shoulders", "triceps"] },
      { name: "Squats", mode: "time", value: 25, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Plank", mode: "time", value: 20, muscle_groups: ["core", "shoulders"] },
      { name: "Glute Bridge", mode: "time", value: 20, muscle_groups: ["glutes", "hamstrings"] },
    ],
  },
  {
    id: "fithub/full-body-hard",
    name: "Full Body Hard",
    description: "Challenging full body grind with longer holds and more rounds.",
    difficulty: "advanced",
    tags: ["full-body", "advanced", "bodyweight", "endurance"],
    equipment: ["none"],
    rounds: 4,
    estimated_duration_min: 25,
    fork_count: 7,
    muscle_groups: ["chest", "shoulders", "triceps", "quads", "glutes", "hamstrings", "core", "lower back"],
    exercises: [
      { name: "Push-Ups", mode: "time", value: 40, muscle_groups: ["chest", "shoulders", "triceps"] },
      { name: "Squats", mode: "time", value: 50, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Plank", mode: "time", value: 40, muscle_groups: ["core", "shoulders"] },
      { name: "Reverse Lunges", mode: "time", value: 40, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Superman", mode: "time", value: 35, muscle_groups: ["lower back", "glutes"] },
      { name: "Glute Bridge", mode: "time", value: 35, muscle_groups: ["glutes", "hamstrings"] },
    ],
  },
  {
    id: "fithub/quick-10min",
    name: "Quick 10min",
    description: "Fast and effective 10-minute session when you're short on time.",
    difficulty: "beginner",
    tags: ["quick", "beginner", "bodyweight", "full-body"],
    equipment: ["none"],
    rounds: 2,
    estimated_duration_min: 5,
    fork_count: 3,
    muscle_groups: ["chest", "shoulders", "triceps", "quads", "glutes", "hamstrings", "core"],
    exercises: [
      { name: "Push-Ups", mode: "time", value: 25, muscle_groups: ["chest", "shoulders", "triceps"] },
      { name: "Squats", mode: "time", value: 30, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Plank", mode: "time", value: 20, muscle_groups: ["core", "shoulders"] },
    ],
  },
  {
    id: "fithub/arnold-golden-era",
    name: "Arnold Golden Era",
    description: "Inspired by Arnold's classic high-volume training, adapted for bodyweight.",
    difficulty: "advanced",
    tags: ["arnold", "volume", "push-pull", "bodyweight", "classic"],
    equipment: ["none"],
    rounds: 4,
    estimated_duration_min: 29,
    fork_count: 12,
    muscle_groups: ["chest", "shoulders", "triceps", "quads", "glutes", "hamstrings", "core", "lower back"],
    exercises: [
      { name: "Push-Ups", mode: "time", value: 45, muscle_groups: ["chest", "shoulders", "triceps"] },
      { name: "Squats", mode: "time", value: 50, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Plank", mode: "time", value: 40, muscle_groups: ["core", "shoulders"] },
      { name: "Reverse Lunges", mode: "time", value: 45, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Superman", mode: "time", value: 35, muscle_groups: ["lower back", "glutes"] },
      { name: "Glute Bridge", mode: "time", value: 40, muscle_groups: ["glutes", "hamstrings"] },
      { name: "Bird Dog", mode: "time", value: 30, muscle_groups: ["core", "lower back"] },
    ],
  },
  {
    id: "fithub/hiit-tabata",
    name: "HIIT Tabata Blaster",
    description: "High intensity interval training with short bursts and minimal rest.",
    difficulty: "advanced",
    tags: ["hiit", "tabata", "cardio", "bodyweight", "fat-burn"],
    equipment: ["none"],
    rounds: 4,
    estimated_duration_min: 14,
    fork_count: 5,
    muscle_groups: ["quads", "glutes", "hamstrings", "chest", "shoulders", "triceps", "core", "lower back"],
    exercises: [
      { name: "Squats", mode: "time", value: 20, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Push-Ups", mode: "time", value: 20, muscle_groups: ["chest", "shoulders", "triceps"] },
      { name: "Reverse Lunges", mode: "time", value: 20, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Plank", mode: "time", value: 20, muscle_groups: ["core", "shoulders"] },
      { name: "Superman", mode: "time", value: 20, muscle_groups: ["lower back", "glutes"] },
    ],
  },
  {
    id: "fithub/calisthenics-basics",
    name: "Calisthenics Basics",
    description: "Foundation calisthenics movements for building bodyweight strength.",
    difficulty: "beginner",
    tags: ["calisthenics", "beginner", "bodyweight", "strength"],
    equipment: ["none"],
    rounds: 3,
    estimated_duration_min: 12,
    fork_count: 3,
    muscle_groups: ["chest", "shoulders", "triceps", "quads", "glutes", "hamstrings", "core", "lower back"],
    exercises: [
      { name: "Push-Ups", mode: "time", value: 25, muscle_groups: ["chest", "shoulders", "triceps"] },
      { name: "Squats", mode: "time", value: 30, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Plank", mode: "time", value: 30, muscle_groups: ["core", "shoulders"] },
      { name: "Glute Bridge", mode: "time", value: 25, muscle_groups: ["glutes", "hamstrings"] },
      { name: "Bird Dog", mode: "time", value: 25, muscle_groups: ["core", "lower back"] },
    ],
  },
  {
    id: "fithub/upper-lower-a",
    name: "Upper/Lower Split A (Upper)",
    description: "Day A of a classic upper/lower split - all upper body pushing and pulling.",
    difficulty: "intermediate",
    tags: ["split", "upper-body", "push-pull", "bodyweight"],
    equipment: ["none"],
    rounds: 3,
    estimated_duration_min: 15,
    fork_count: 2,
    muscle_groups: ["chest", "shoulders", "triceps", "core", "obliques", "lower back"],
    exercises: [
      { name: "Push-Ups", mode: "time", value: 35, muscle_groups: ["chest", "shoulders", "triceps"] },
      { name: "Plank", mode: "time", value: 35, muscle_groups: ["core", "shoulders"] },
      { name: "Superman", mode: "time", value: 30, muscle_groups: ["lower back", "glutes"] },
      { name: "Side Plank Left", mode: "time", value: 20, muscle_groups: ["core", "obliques"] },
      { name: "Side Plank Right", mode: "time", value: 20, muscle_groups: ["core", "obliques"] },
      { name: "Bird Dog", mode: "time", value: 25, muscle_groups: ["core", "lower back"] },
    ],
  },
  {
    id: "fithub/upper-lower-b",
    name: "Upper/Lower Split B (Lower)",
    description: "Day B of a classic upper/lower split - legs, glutes, and posterior chain.",
    difficulty: "intermediate",
    tags: ["split", "lower-body", "legs", "bodyweight"],
    equipment: ["none"],
    rounds: 3,
    estimated_duration_min: 14,
    fork_count: 2,
    muscle_groups: ["quads", "glutes", "hamstrings"],
    exercises: [
      { name: "Squats", mode: "time", value: 40, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Reverse Lunges", mode: "time", value: 35, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Glute Bridge", mode: "time", value: 35, muscle_groups: ["glutes", "hamstrings"] },
      { name: "Squats", mode: "time", value: 35, muscle_groups: ["quads", "glutes", "hamstrings"] },
      { name: "Glute Bridge", mode: "time", value: 30, muscle_groups: ["glutes", "hamstrings"] },
    ],
  },
];

export function getWorkoutBySlug(slug: string): OpenWorkout | undefined {
  return WORKOUTS.find((w) => w.id.split("/")[1] === slug);
}

export function getSlug(workout: OpenWorkout): string {
  return workout.id.split("/")[1];
}
