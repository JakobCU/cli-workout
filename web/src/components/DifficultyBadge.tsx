interface DifficultyBadgeProps {
  difficulty: "beginner" | "intermediate" | "advanced";
  size?: "sm" | "md";
}

const config = {
  beginner: {
    bg: "bg-green-500/15",
    text: "text-green-400",
    border: "border-green-500/30",
    label: "Beginner",
  },
  intermediate: {
    bg: "bg-yellow-500/15",
    text: "text-yellow-400",
    border: "border-yellow-500/30",
    label: "Intermediate",
  },
  advanced: {
    bg: "bg-red-500/15",
    text: "text-red-400",
    border: "border-red-500/30",
    label: "Advanced",
  },
};

export function DifficultyBadge({ difficulty, size = "sm" }: DifficultyBadgeProps) {
  const c = config[difficulty];
  const sizeClasses = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";
  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${c.bg} ${c.text} ${c.border} ${sizeClasses}`}
    >
      {c.label}
    </span>
  );
}
