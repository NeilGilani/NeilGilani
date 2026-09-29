"""Markets: how the six repos fit together (verified from each repo's imports)."""
import sys
from diagram import Diagram
from svgkit import DARK, LIGHT


def build(T):
    d = Diagram(T, 1200, 560, title="The markets stack",
                desc="quant-research, quantlang and exchange-simulator all import quantsim, which holds the "
                     "Monte Carlo engine, the no-lookahead backtester, order-book execution and paper trading. "
                     "stratlab and optionslab stand alone.")
    d.background()
    d.heading("MARKETS · SIX REPOS, ONE STACK", "The research runs on engines built and tested first.")

    # consumers of quantsim
    d.group(36, 128, 776, 400, "Python · pip-installable")
    r = d.node(60, 152, 232, 108, "quant-research", ["Martingale notes 001–006", "out-of-sample registry", "alpha-lab"], accent=True)
    q = d.node(312, 152, 232, 108, "quantlang", ["strategy language:", "lexer → parser →", "validator → interpreter"])
    x = d.node(564, 152, 224, 108, "exchange-simulator", ["heterogeneous agents", "funding network", "fragility under shocks"])

    # quantsim core with its modules
    core = d.node(60, 316, 728, 188, "quantsim", "one Strategy object from research to paper trading", accent=True)
    mods = [("simulate.py", ["Monte Carlo", "risk metrics"]), ("backtest.py", ["event-driven", "daily loop"]),
            ("execution.py", ["what a trade", "really costs"]), ("orderbook.py", ["price-time", "priority"]),
            ("live.py", ["paper trading", "sim or Alpaca"])]
    mx, mw, gap = 76, 132, 9
    for i, (name, sub) in enumerate(mods):
        d.node(mx + i * (mw + gap), 392, mw, 96, name, sub, accent=(name == "orderbook.py"))

    for n, lab in ((r, "imports"), (q, "compiles to Strategy"), (x, "matching engine")):
        d.edge([(n["b"][0], n["b"][1]), (n["b"][0], core["y"])], lab, lpos=(n["b"][0], 288))

    # standalone
    d.group(844, 128, 320, 400, "Standalone")
    d.node(868, 152, 272, 150, "stratlab", ["plain English → StratLang", "no-lookahead backtester", "ported to JavaScript,", "runs in the browser"])
    d.node(868, 330, 272, 174, "optionslab", ["Black–Scholes · CRR tree ·", "Monte Carlo: three engines", "that must agree", "Greeks · implied vol", "American exercise"])
    return d.render()


if __name__ == "__main__":
    out = sys.argv[1]
    for T in (DARK, LIGHT):
        open(f"{out}/markets-stack-{T.name}.svg", "w").write(build(T))
    print("ok")
