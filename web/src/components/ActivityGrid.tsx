import { useState, useMemo } from 'react'

function generateActivityData(): Map<string, number> {
  const data = new Map<string, number>();
  const now = new Date();
  const seed = 42;
  let rng = seed;

  function nextRandom() {
    rng = (rng * 16807 + 0) % 2147483647;
    return rng / 2147483647;
  }

  // Generate ~50 sessions over the past 365 days with realistic patterns
  // More frequent recently, some streaks, some gaps
  for (let i = 0; i < 365; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    // Higher probability for recent days
    const recencyBoost = 1 - (i / 365) * 0.6;
    const dayOfWeek = date.getDay();
    // Weekdays more likely
    const dayBoost = dayOfWeek >= 1 && dayOfWeek <= 5 ? 1.2 : 0.7;

    const prob = 0.12 * recencyBoost * dayBoost;

    if (nextRandom() < prob) {
      // 1-4 sessions that day
      const sessions = nextRandom() < 0.3 ? (nextRandom() < 0.5 ? 3 : 2) : 1;
      data.set(dateStr, sessions);

      // Streak logic: if we worked out, 40% chance next day too
      if (nextRandom() < 0.4 && i > 0) {
        const streakDate = new Date(now);
        streakDate.setDate(streakDate.getDate() - i + 1);
        const streakStr = streakDate.toISOString().split('T')[0];
        if (!data.has(streakStr)) {
          data.set(streakStr, nextRandom() < 0.5 ? 2 : 1);
        }
      }
    }
  }

  return data;
}

function getIntensityColor(count: number): string {
  if (count === 0) return 'bg-zinc-800';
  if (count === 1) return 'bg-green-900';
  if (count === 2) return 'bg-green-700';
  return 'bg-green-500';
}

function getIntensityColorHex(count: number): string {
  if (count === 0) return '#27272a';
  if (count === 1) return '#14532d';
  if (count === 2) return '#15803d';
  return '#22c55e';
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DAYS = ['Mon', '', 'Wed', '', 'Fri', '', ''];

interface DayData {
  date: string;
  count: number;
  dayOfWeek: number;
}

export function ActivityGrid() {
  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);

  const { weeks, monthLabels } = useMemo(() => {
    const activityData = generateActivityData();
    const now = new Date();
    const weeksArr: DayData[][] = [];

    // Build 52 weeks of data ending today
    // Find the most recent Saturday (end of week)
    const endDate = new Date(now);
    // Go to the start: 52 weeks * 7 days ago, aligned to Sunday
    const startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - (52 * 7) - endDate.getDay());

    const currentDate = new Date(startDate);
    let currentWeek: DayData[] = [];

    while (currentDate <= endDate) {
      const dateStr = currentDate.toISOString().split('T')[0];
      const dayOfWeek = currentDate.getDay();

      if (dayOfWeek === 0 && currentWeek.length > 0) {
        weeksArr.push(currentWeek);
        currentWeek = [];
      }

      currentWeek.push({
        date: dateStr,
        count: activityData.get(dateStr) || 0,
        dayOfWeek,
      });

      currentDate.setDate(currentDate.getDate() + 1);
    }
    if (currentWeek.length > 0) {
      weeksArr.push(currentWeek);
    }

    // Build month labels
    const labels: { label: string; col: number }[] = [];
    let lastMonth = -1;
    weeksArr.forEach((week, weekIdx) => {
      const firstDay = week[0];
      if (firstDay) {
        const month = new Date(firstDay.date).getMonth();
        if (month !== lastMonth) {
          labels.push({ label: MONTHS[month], col: weekIdx });
          lastMonth = month;
        }
      }
    });

    return { weeks: weeksArr, monthLabels: labels };
  }, []);

  const totalSessions = useMemo(() => {
    let total = 0;
    weeks.forEach(week => week.forEach(day => { total += day.count; }));
    return total;
  }, [weeks]);

  return (
    <div className="w-full">
      <div className="flex items-baseline justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">
          <span className="text-zinc-400">{totalSessions}</span> sessions in the last year
        </h3>
      </div>

      <div className="overflow-x-auto pb-2">
        <div className="inline-block min-w-fit">
          {/* Month labels */}
          <div className="flex ml-8 mb-1">
            {monthLabels.map((m, i) => {
              const nextCol = monthLabels[i + 1]?.col ?? weeks.length;
              const span = nextCol - m.col;
              return (
                <div
                  key={`${m.label}-${m.col}`}
                  className="text-xs text-zinc-500"
                  style={{ width: `${span * 14}px` }}
                >
                  {span >= 2 ? m.label : ''}
                </div>
              );
            })}
          </div>

          {/* Grid */}
          <div className="flex gap-0">
            {/* Day labels */}
            <div className="flex flex-col gap-[3px] mr-1 justify-start">
              {DAYS.map((d, i) => (
                <div key={i} className="h-[11px] text-[10px] leading-[11px] text-zinc-500 w-6 text-right pr-1">
                  {d}
                </div>
              ))}
            </div>

            {/* Weeks */}
            <div className="flex gap-[3px]">
              {weeks.map((week, weekIdx) => (
                <div key={weekIdx} className="flex flex-col gap-[3px]">
                  {[0, 1, 2, 3, 4, 5, 6].map((dayIdx) => {
                    const day = week.find(d => d.dayOfWeek === dayIdx);
                    if (!day) {
                      return <div key={dayIdx} className="w-[11px] h-[11px]" />;
                    }
                    return (
                      <div
                        key={dayIdx}
                        className={`w-[11px] h-[11px] rounded-sm ${getIntensityColor(day.count)} cursor-pointer transition-all hover:ring-1 hover:ring-zinc-500`}
                        onMouseEnter={(e) => {
                          const rect = e.currentTarget.getBoundingClientRect();
                          const parentRect = e.currentTarget.closest('.overflow-x-auto')?.getBoundingClientRect();
                          if (parentRect) {
                            setTooltip({
                              x: rect.left - parentRect.left + rect.width / 2,
                              y: rect.top - parentRect.top - 8,
                              text: `${day.count} session${day.count !== 1 ? 's' : ''} on ${new Date(day.date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`,
                            });
                          }
                        }}
                        onMouseLeave={() => setTooltip(null)}
                      />
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center justify-end mt-2 gap-1.5">
            <span className="text-[10px] text-zinc-500 mr-1">Less</span>
            {[0, 1, 2, 3].map((level) => (
              <div
                key={level}
                className="w-[11px] h-[11px] rounded-sm"
                style={{ backgroundColor: getIntensityColorHex(level) }}
              />
            ))}
            <span className="text-[10px] text-zinc-500 ml-1">More</span>
          </div>
        </div>

        {/* Tooltip */}
        {tooltip && (
          <div
            className="absolute pointer-events-none z-10 px-2 py-1 bg-zinc-700 text-white text-xs rounded shadow-lg whitespace-nowrap -translate-x-1/2 -translate-y-full"
            style={{ left: tooltip.x, top: tooltip.y }}
          >
            {tooltip.text}
          </div>
        )}
      </div>
    </div>
  );
}
