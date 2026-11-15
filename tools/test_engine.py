import sys, random, math
sys.path.insert(0, "plugin")
import pinball_engine as pe

def run(seed, skill):
    random.seed(seed)
    g = pe.Pinball(); g.new_game()
    t = 0; dt = 0.033; launches = 0; maxsp = 0; exits = []
    minx = miny = 1e9; maxx = maxy = -1e9
    while g.state != g.OVER and t < 900:
        if g.state == g.READY:
            if not g.charging:
                g.plunger_press(); hold = random.uniform(0.05, 1.0); ht = 0
            else:
                ht += dt
                if ht >= hold: g.plunger_release(); launches += 1
        # bot: flip when ball is near a flipper (with skill probability)
        for i, f in enumerate(g.flippers):
            near = abs(g.bx - (f.px + f.sign * 35)) < 45 and 570 < g.by < 640
            g.set_flipper(i, near and random.random() < skill)
        g.update(dt); t += dt
        if g.state == g.PLAY:
            assert g.bx == g.bx and g.by == g.by
            minx = min(minx, g.bx); maxx = max(maxx, g.bx); miny = min(miny, g.by); maxy = max(maxy, g.by)
            maxsp = max(maxsp, math.hypot(g.vx, g.vy))
            # must stay inside table outline (above drain)
            if g.by < 690:
                assert 10 - 1 <= g.bx - pe.R + 1 and g.bx + pe.R - 1 <= 410 + 1, (g.bx, g.by)
                if g.by < 210:
                    assert math.hypot(g.bx - 210, g.by - 210) <= 200 - pe.R + 2, (g.bx, g.by)
    return g.score, round(t), launches, round(maxsp), (round(minx), round(maxx), round(miny), round(maxy)), g.mult

for skill in (0.0, 0.5, 0.9):
    for seed in range(6):
        print(skill, seed, run(seed, skill))
