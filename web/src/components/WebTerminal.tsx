import { useEffect, useRef } from 'react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

// ANSI color helpers
const R = '\x1b[0m'
const BOLD = '\x1b[1m'
const DIM = '\x1b[2m'
const CYAN = '\x1b[96m'
const GREEN = '\x1b[92m'
const YELLOW = '\x1b[93m'
const RED = '\x1b[91m'
const WHITE = '\x1b[97m'
const B_CYAN = `${BOLD}${CYAN}`
const B_GREEN = `${BOLD}${GREEN}`
const B_YELLOW = `${BOLD}${YELLOW}`
const B_RED = `${BOLD}${RED}`
const B_WHITE = `${BOLD}${WHITE}`

const BANNER = `
${B_CYAN}   ____ _ _   _____ _ _
  / ___(_) |_|  ___(_) |_
 | |  _| | __| |_  | | __|
 | |_| | | |_|  _| | | |_
  \\____|_|\\__|_|   |_|\\__|${R}
`

const BLOBBY_WARRIOR = `${B_YELLOW}        \\\\  /
     .-''''-.
    / @    @ \\\\
   |  (~~~~)  |
    \\\\ \`----' /
     '------'
    /|        |\\\\
   / |  IRON  | \\\\
     |________|
      ||    ||
     _||_  _||_${R}`

const MAIN_MENU = (next: string) => `
  ${B_YELLOW}Iron Blobby${R}  |  ${B_CYAN}Lv.5 Warrior${R}  |  ${B_RED}Streak: 4d${R}
  ${B_YELLOW}1850XP${R} ${CYAN}${'#'.repeat(11)}${'·'.repeat(4)}${R} ${DIM}150 to Elite${R}
  ${DIM}Next: ${B_YELLOW}${next}${R}  |  Session #48${R}

  ${CYAN}1)${R} Start workout    ${CYAN}4)${R} History    ${CYAN}7)${R} Weekly plan
  ${CYAN}2)${R} Workouts         ${CYAN}5)${R} Stats      ${CYAN}8)${R} AI Coach
  ${CYAN}3)${R} Exercises        ${CYAN}6)${R} Achievements ${CYAN}9)${R} Config
  ${CYAN}0)${R} Quit
`

const HISTORY_OUTPUT = `${B_CYAN}  History${R}  ${DIM}(last 5 sessions)${R}

  ${DIM}┌──────────────────┬────────────┬──────────┬──────────────┐${R}
  ${DIM}│${R} ${B_WHITE}Date${R}             ${DIM}│${R} ${B_WHITE}Workout${R}    ${DIM}│${R} ${B_WHITE}Duration${R} ${DIM}│${R} ${B_WHITE}Notes${R}        ${DIM}│${R}
  ${DIM}├──────────────────┼────────────┼──────────┼──────────────┤${R}
  ${DIM}│${R} 2026-03-15 08:30 ${DIM}│${R} ${YELLOW}Workout A${R}  ${DIM}│${R} ${GREEN}18 min${R}   ${DIM}│${R} felt strong  ${DIM}│${R}
  ${DIM}│${R} 2026-03-14 07:45 ${DIM}│${R} ${YELLOW}Workout B${R}  ${DIM}│${R} ${GREEN}16 min${R}   ${DIM}│${R}              ${DIM}│${R}
  ${DIM}│${R} 2026-03-13 08:00 ${DIM}│${R} ${YELLOW}Workout C${R}  ${DIM}│${R} ${GREEN}20 min${R}   ${DIM}│${R} pushed hard  ${DIM}│${R}
  ${DIM}│${R} 2026-03-12 07:30 ${DIM}│${R} ${YELLOW}Workout A${R}  ${DIM}│${R} ${GREEN}17 min${R}   ${DIM}│${R}              ${DIM}│${R}
  ${DIM}│${R} 2026-03-10 08:15 ${DIM}│${R} ${YELLOW}Workout B${R}  ${DIM}│${R} ${GREEN}15 min${R}   ${DIM}│${R}              ${DIM}│${R}
  ${DIM}└──────────────────┴────────────┴──────────┴──────────────┘${R}
`

const STATS_OUTPUT = `${B_CYAN}  Stats${R}

  Sessions   : ${B_GREEN}47${R}
  XP         : ${B_YELLOW}1850${R}
  Level      : ${B_CYAN}5 - Warrior${R}
  Streak     : ${B_RED}4 days${R}  (best: 12)
  Workouts   : 2 configured
  Achievements: ${B_GREEN}5 / 15 unlocked${R}

  ${B_YELLOW}Exercise Progression:${R}
    Push-Ups  : ${GREEN}+10s${R}
    Squats    : ${GREEN}+15s${R}
    Plank     : ${GREEN}+5s${R}
`

const EXERCISES_BROWSE = `${B_CYAN}  Exercise Browser${R}  ${DIM}1/9${R}

${B_YELLOW}  Push-Ups${R}
  ${DIM}push-ups${R}

  Classic upper body exercise targeting chest, shoulders, and triceps.

${B_GREEN}               \\\\  /
            .-''''-.
           / @    @ \\\\
          |  (~~~~)  |
           \\\\ \`----' /    __/
        ----\`------'----'
       /  /            \\\\  \\\\
      +--+              +--+
     _|  |______________|  |_
    /////              \\\\\\\\\\\\${R}

  Muscle groups: ${B_YELLOW}chest, shoulders, triceps${R}
  Default: 30s

  ${CYAN}Tips:${R}
    - Keep core tight throughout the movement
    - Lower chest to the ground, not your hips
    - Breathe in going down, out pushing up

  ${CYAN}Variants:${R}
    ${B_YELLOW}Wide Push-Ups${R}  ${DIM}Wider hand placement for more chest activation${R}
    ${B_YELLOW}Diamond Push-Ups${R}  ${DIM}Hands together for tricep focus${R}
    ${B_YELLOW}Decline Push-Ups${R}  ${DIM}Feet elevated for upper chest${R}

  ${CYAN}n)${R} Next    ${CYAN}p)${R} Previous    ${CYAN}a)${R} Animate    ${CYAN}q)${R} Back
`

const EXERCISES_2 = `${B_CYAN}  Exercise Browser${R}  ${DIM}2/9${R}

${B_YELLOW}  Squats${R}
  ${DIM}squats${R}

  Fundamental lower body exercise targeting quads, glutes, and hamstrings.

${B_GREEN}            \\\\  /
         .-''''-.
        / @    @ \\\\
       |  (~~~~)  |
        \\\\ \`----' /
         '------'
           |  |
          /|  |\\\\
         / |  | \\\\
        /  |  |  \\\\
       /  _|  |_  \\\\
      /__/      \\\\__\\\\${R}

  Muscle groups: ${B_YELLOW}quads, glutes, hamstrings${R}
  Default: 40s

  ${CYAN}Tips:${R}
    - Keep weight on heels, knees tracking over toes
    - Go as low as comfortable with good form
    - Drive up through your heels

  ${CYAN}n)${R} Next    ${CYAN}p)${R} Previous    ${CYAN}a)${R} Animate    ${CYAN}q)${R} Back
`

const AI_MENU = `${B_CYAN}  AI Features${R}

  Provider: ${B_GREEN}openai${R}    API Key: ${B_GREEN}configured${R}    SDK: ${B_GREEN}installed${R}

  ${CYAN}1)${R}  Coach -- get personalized advice
  ${CYAN}2)${R}  Generate workout -- create a workout from a description
  ${CYAN}3)${R}  Generate exercise -- create an exercise with ASCII art
  ${CYAN}4)${R}  Adapt -- AI tweaks your existing workouts
  ${CYAN}5)${R}  Setup API key / provider
  ${CYAN}6)${R}  Back
`

const AI_COACH_OUTPUT = `${BLOBBY_WARRIOR}
  ${B_YELLOW}Blobby is thinking...${R}

`

const AI_COACH_STREAM = `Hey there, champion! ${B_YELLOW}*flexes tiny blob arms*${R}

Looking at your data, I'm impressed -- 47 sessions and a Level 5 Warrior! Your consistency has been solid with a 4-day streak going. You're hitting about 3-4 sessions per week which matches your target perfectly.

${B_CYAN}Here's what I'd tweak:${R}

1. ${B_GREEN}Add variety${R} -- You've been rotating A/B/C workouts which is great, but your upper body progression (+10s on Push-Ups) is outpacing your core (+5s on Plank). Consider adding a dedicated core day.

2. ${B_YELLOW}Push the squats${R} -- Your +15s squat progression shows strong legs. Time to try the ${CYAN}Full Body Hard${R} workout from the library to keep challenging yourself.

3. ${B_GREEN}Keep the streak alive${R} -- You're 4 days in. Hit day 7 and you'll unlock the ${YELLOW}Week Warrior${R} achievement!

${B_YELLOW}*Blobby bounces excitedly*${R} You're doing amazing -- let's keep this momentum going! 💪

${DIM}[DEMO -- AI responses are simulated on this page]${R}
`

const AI_GENERATE_OUTPUT = `  ${B_YELLOW}Blobby is designing your exercise...${R}

  ${B_YELLOW}Burpees${R}
  ${DIM}burpees${R}

  Full-body explosive exercise combining a squat, plank, and jump.

  Muscles: ${CYAN}quads, chest, core, shoulders${R}
  Default: 30s

  ${B_GREEN}Generating ASCII animation...${R}
  Animation: ${B_GREEN}4 custom frames generated${R}

  ${DIM}Frame 0 preview:${R}
${B_YELLOW}            \\\\  /
         .-''''-.
        / ^    ^ \\\\      *
       |  (~~~~)  |
        \\\\ \`----' /
         '------'
           |  |
          /    \\\\
         /      \\\\
        /________\\\\${R}

  Tips:
    - Land softly to protect your joints
    - Keep core engaged during the plank phase
    - Modify by removing the jump if needed

  ${DIM}[DEMO -- exercise would be saved to exercises/burpees.exercise.gitfit]${R}
`

const ACHIEVEMENTS_OUTPUT = `${B_CYAN}  Achievements${R}  ${DIM}5 / 15 unlocked${R}

  ${B_GREEN}★${R} First Step       ${DIM}-- Complete your first session${R}
  ${B_GREEN}★${R} Streak 3         ${DIM}-- 3-day streak${R}
  ${B_GREEN}★${R} Week Warrior     ${DIM}-- 7-day streak${R}
  ${B_GREEN}★${R} Dedicated        ${DIM}-- Complete 10 sessions${R}
  ${B_GREEN}★${R} Committed        ${DIM}-- Complete 25 sessions${R}
  ${DIM}☆ Half Century     -- Complete 50 sessions${R}
  ${DIM}☆ Century          -- Complete 100 sessions${R}
  ${DIM}☆ Streak 14        -- 14-day streak${R}
  ${DIM}☆ Streak 30        -- 30-day streak${R}
  ${DIM}☆ XP 1000          -- Earn 1000 XP${R}
  ${DIM}☆ XP 5000          -- Earn 5000 XP${R}
  ${DIM}☆ Endurance 30     -- Single session over 30 min${R}
  ${DIM}☆ Endurance 60     -- Single session over 60 min${R}
  ${DIM}☆ All Workouts     -- Complete every workout type${R}
  ${DIM}☆ Forker           -- Fork 5 workouts from the library${R}
`

type Screen = 'main' | 'history' | 'stats' | 'exercises' | 'exercises2' | 'achievements' | 'ai' | 'ai_coach' | 'ai_generate' | 'quit'

const WS_URL = import.meta.env.VITE_WS_URL || ''

export function WebTerminal() {
  const termRef = useRef<HTMLDivElement>(null)
  const modeRef = useRef<'live' | 'demo'>('demo')
  const wsRef = useRef<WebSocket | null>(null)
  const dataHandlerRef = useRef<{ dispose: () => void } | null>(null)
  const initRef = useRef(false)
  const stateRef = useRef<{ screen: Screen; inputBuf: string; term: Terminal | null }>({
    screen: 'main',
    inputBuf: '',
    term: null,
  })

  useEffect(() => {
    if (!termRef.current || initRef.current) return
    initRef.current = true

    const term = new Terminal({
      theme: {
        background: '#09090b',
        foreground: '#d4d4d8',
        cursor: '#22c55e',
        cursorAccent: '#09090b',
        selectionBackground: '#22c55e33',
        black: '#09090b',
        red: '#f87171',
        green: '#4ade80',
        yellow: '#facc15',
        blue: '#60a5fa',
        magenta: '#c084fc',
        cyan: '#22d3ee',
        white: '#d4d4d8',
        brightBlack: '#71717a',
        brightRed: '#fca5a5',
        brightGreen: '#86efac',
        brightYellow: '#fde047',
        brightBlue: '#93c5fd',
        brightMagenta: '#d8b4fe',
        brightCyan: '#67e8f9',
        brightWhite: '#fafafa',
      },
      fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", Menlo, Monaco, monospace',
      fontSize: 13,
      lineHeight: 1.2,
      cursorBlink: true,
      cols: 80,
      rows: 30,
      scrollback: 1000,
      convertEol: true,
    })

    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(termRef.current)
    try { fitAddon.fit() } catch { /* ok */ }

    stateRef.current.term = term
    let settled = false // prevent race between timeout and onopen

    // Try live WebSocket connection first
    if (WS_URL) {
      tryLiveMode(term)
    } else {
      startDemoMode(term)
    }

    function setDataHandler(handler: (data: string) => void) {
      // Dispose any existing handler before registering a new one
      if (dataHandlerRef.current) {
        dataHandlerRef.current.dispose()
      }
      dataHandlerRef.current = term.onData(handler)
    }

    function tryLiveMode(t: Terminal) {
      const ws = new WebSocket(WS_URL)
      const timeout = setTimeout(() => {
        if (!settled) { settled = true; ws.close(); startDemoMode(t) }
      }, 3000)

      ws.onopen = () => {
        if (settled) { ws.close(); return }
        settled = true
        clearTimeout(timeout)
        modeRef.current = 'live'
        wsRef.current = ws
        // Local echo only -- PTY echo is disabled server-side
        setDataHandler((data) => {
          if (ws.readyState !== WebSocket.OPEN) return
          // Echo printable chars, enter, backspace locally
          for (const ch of data) {
            if (ch === '\r') t.write('\r\n')
            else if (ch === '\x7f' || ch === '\b') t.write('\b \b')
            else if (ch >= ' ') t.write(ch)
          }
          ws.send(data)
        })
      }
      ws.onmessage = (e) => t.write(e.data)
      ws.onclose = () => {
        if (!settled) { settled = true; clearTimeout(timeout); startDemoMode(t) }
        else if (modeRef.current === 'live') {
          t.write('\r\n\x1b[90m--- Session ended. Refresh to restart. ---\x1b[0m\r\n')
        }
      }
      ws.onerror = () => {
        if (!settled) { settled = true; clearTimeout(timeout); startDemoMode(t) }
      }
    }

    function startDemoMode(_t: Terminal) {
      modeRef.current = 'demo'
      setDataHandler((data) => { handleInput(stateRef.current.screen, data) })
      showScreen('main')
    }

    function showScreen(screen: Screen) {
      stateRef.current.screen = screen
      stateRef.current.inputBuf = ''
      term.write('\x1b[2J\x1b[H') // clear
      switch (screen) {
        case 'main':
          term.write(BANNER)
          term.write(MAIN_MENU('Workout A'))
          prompt()
          break
        case 'history':
          term.write(HISTORY_OUTPUT)
          term.write(`\r\n  ${DIM}Press Enter to go back${R}\r\n`)
          break
        case 'stats':
          term.write(STATS_OUTPUT)
          term.write(`\r\n  ${DIM}Press Enter to go back${R}\r\n`)
          break
        case 'exercises':
          term.write(EXERCISES_BROWSE)
          prompt()
          break
        case 'exercises2':
          term.write(EXERCISES_2)
          prompt()
          break
        case 'achievements':
          term.write(ACHIEVEMENTS_OUTPUT)
          term.write(`\r\n  ${DIM}Press Enter to go back${R}\r\n`)
          break
        case 'ai':
          term.write(AI_MENU)
          prompt()
          break
        case 'ai_coach':
          term.write(AI_COACH_OUTPUT)
          streamText(AI_COACH_STREAM, () => {
            term.write(`\r\n  ${DIM}Press Enter to go back${R}\r\n`)
          })
          return
        case 'ai_generate':
          term.write(`\r\n  Describe your exercise: ${B_GREEN}burpees with jump${R}\r\n`)
          setTimeout(() => {
            term.write(AI_GENERATE_OUTPUT)
            term.write(`\r\n  ${DIM}Press Enter to go back${R}\r\n`)
          }, 800)
          return
        case 'quit':
          term.write(`\r\n  ${B_GREEN}Stay consistent. See you next time!${R}\r\n\r\n`)
          term.write(`  ${DIM}$ █${R}`)
          return
      }
    }

    function prompt() {
      term.write(`\r\n  Select: `)
    }

    function streamText(text: string, onDone: () => void) {
      let i = 0
      const interval = setInterval(() => {
        // Write a few chars at a time for speed
        const chunk = text.slice(i, i + 3)
        if (!chunk) {
          clearInterval(interval)
          onDone()
          return
        }
        term.write(chunk)
        i += 3
      }, 15)
    }

    function handleInput(screen: Screen, key: string) {
      if (screen === 'quit') return

      // Enter on info screens goes back
      if (['history', 'stats', 'achievements'].includes(screen)) {
        if (key === '\r') showScreen('main')
        return
      }

      if (screen === 'ai_coach' || screen === 'ai_generate') {
        if (key === '\r') showScreen('ai')
        return
      }

      // Backspace
      if (key === '\x7f') {
        if (stateRef.current.inputBuf.length > 0) {
          stateRef.current.inputBuf = stateRef.current.inputBuf.slice(0, -1)
          term.write('\b \b')
        }
        return
      }

      // Enter -- process command
      if (key === '\r') {
        const cmd = stateRef.current.inputBuf.trim()
        stateRef.current.inputBuf = ''
        term.write('\r\n')

        if (screen === 'main') {
          switch (cmd) {
            case '3': showScreen('exercises'); break
            case '4': showScreen('history'); break
            case '5': showScreen('stats'); break
            case '6': showScreen('achievements'); break
            case '8': showScreen('ai'); break
            case '0': showScreen('quit'); break
            default:
              if (['1', '2', '7', '9'].includes(cmd)) {
                term.write(`  ${DIM}Feature available in the full CLI: pip install gitfit${R}\r\n`)
                setTimeout(() => showScreen('main'), 1200)
              } else {
                term.write(`  ${RED}Invalid choice.${R}\r\n`)
                setTimeout(() => showScreen('main'), 600)
              }
          }
        } else if (screen === 'exercises') {
          switch (cmd) {
            case 'n': showScreen('exercises2'); break
            case 'q': case 'b': case '': showScreen('main'); break
            case 'a':
              term.write(`  ${DIM}Animation plays for 5s in the full CLI...${R}\r\n`)
              setTimeout(() => showScreen('exercises'), 1000)
              break
            default: showScreen('exercises'); break
          }
        } else if (screen === 'exercises2') {
          switch (cmd) {
            case 'n': showScreen('exercises'); break
            case 'p': showScreen('exercises'); break
            case 'q': case 'b': case '': showScreen('main'); break
            default: showScreen('exercises2'); break
          }
        } else if (screen === 'ai') {
          switch (cmd) {
            case '1': showScreen('ai_coach'); break
            case '3': showScreen('ai_generate'); break
            case '6': case '': showScreen('main'); break
            default:
              if (['2', '4', '5'].includes(cmd)) {
                term.write(`  ${DIM}Available in the full CLI with your API key${R}\r\n`)
                setTimeout(() => showScreen('ai'), 1000)
              } else {
                showScreen('ai')
              }
          }
        }
        return
      }

      // Printable character
      if (key.length === 1 && key >= ' ') {
        stateRef.current.inputBuf += key
        term.write(key)
      }
    }

    term.onData((data) => {
      handleInput(stateRef.current.screen, data)
    })

    // Start
    showScreen('main')

    const resizeObserver = new ResizeObserver(() => {
      try { fitAddon.fit() } catch { /* ok */ }
    })
    if (termRef.current) resizeObserver.observe(termRef.current)

    return () => {
      resizeObserver.disconnect()
      wsRef.current?.close()
      term.dispose()
    }
  }, [])

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden shadow-2xl shadow-green-500/5">
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500/70" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
          <div className="w-3 h-3 rounded-full bg-green-500/70" />
          <span className="ml-2 text-xs text-zinc-600 font-mono">gitfit demo</span>
        </div>
        <span className="text-xs text-zinc-600">type a number + Enter to navigate</span>
      </div>
      <div ref={termRef} style={{ padding: '4px', background: '#09090b' }} />
    </div>
  )
}
