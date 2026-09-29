"""HEBB: how the Claude Code plugin learns (from hooks/hooks.json + hooks/hebb_hooks.py)."""
import sys
from diagram import Diagram
from svgkit import DARK, LIGHT, line


def build(T):
    d = Diagram(T, 1200, 600, title="How the Hebb plugin learns",
                desc="Claude Code hooks observe shell commands, pair a failure with the fix that worked, "
                     "and deny known-bad commands before they run, handing back the command that works.")
    d.background()
    d.heading("HEBB · CLAUDE CODE PLUGIN · hooks/hebb_hooks.py",
              "A failure followed by a fix becomes a lesson. Next time the bad command never runs.")

    d.group(36, 128, 560, 440, "Claude Code session · hook → subcommand")
    d.node(60, 152, 512, 72, "SessionStart  →  session", "no key yet? tell the user how to connect")
    n2 = d.node(60, 244, 512, 72, "UserPromptSubmit  →  inject", "relevant lessons and rules into context")
    n3 = d.node(60, 336, 512, 96, "PreToolUse · Bash  →  guard",
                ["deny a banned command outright", "deny a known-bad one, hand back the one that works"],
                accent=True)
    n4 = d.node(60, 452, 512, 92, "PostToolUse · Bash  →  observe",
                ["a command failed, then a variant worked:", "keep the pair as a lesson"], accent=True)

    mx, mw = 672, 244
    m = d.node(mx, 244, mw, 300, "Hebb memory",
               ["hosted API · /v1", "", "lessons", "rules (never_run)", "memories", "",
                "every fact keeps its age", "shared across agents"], accent=True)

    # three straight arrows between the hooks and memory
    d.edge([(mx, n2["r"][1]), (n2["r"][0], n2["r"][1])], "lessons", lpos=(622, n2["r"][1]))
    d.edge([(mx, n3["r"][1]), (n3["r"][0], n3["r"][1])], "rules", accent=True, lpos=(622, n3["r"][1]))
    d.edge([(n4["r"][0], n4["r"][1]), (mx, n4["r"][1])], "new lesson", accent=True, lpos=(622, n4["r"][1]))

    apps = d.node(972, 140, 192, 88, "Other AI apps", ["Claude · ChatGPT", "Gemini · Cursor"], muted=True)
    mcp = d.node(972, 252, 192, 96, "MCP connector", ["/v1/mcp", "remember · recall", "forget · share"])
    team = d.node(972, 452, 192, 92, "Your team", ["shared lessons", "owner approval"])

    d.raw("edge", line(apps["b"][0], apps["b"][1], mcp["t"][0], mcp["t"][1], T.text3, 1.3))
    d.raw("edge", line(mx + mw, 292, 972, 292, T.text3, 1.3))
    d.edge([(mx + mw, team["l"][1]), (972, team["l"][1])], "share", lpos=(944, team["l"][1]))
    return d.render()


if __name__ == "__main__":
    out = sys.argv[1]
    for T in (DARK, LIGHT):
        open(f"{out}/hebb-loop-{T.name}.svg", "w").write(build(T))
    print("ok")
