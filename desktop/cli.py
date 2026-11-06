"""Phase-1 command line, standing in for the UI.

    python -m desktop.cli import-laravel
    python -m desktop.cli create --title "T" --text "One. Two. Three." [--aspect 9:16]
    python -m desktop.cli render <story_id>
    python -m desktop.cli show <story_id>
"""
import argparse
import re
import sys
import time

from desktop.core import db, import_laravel, paths, settings
from desktop.pipeline import images, worker


def _boot():
    settings.seed_from_env(paths.REPO_ROOT / ".env")
    db.init_db()


def cmd_import(_):
    counts = import_laravel.import_laravel(paths.REPO_ROOT, db.Session)
    print("already imported" if counts is None else f"imported {counts}")


def cmd_create(a):
    sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", a.text) if len(x.strip()) >= 3]
    with db.Session() as s:
        st = db.Story(title=a.title, content=a.text, aspect_ratio=a.aspect, style=a.style)
        st.scenes = [db.Scene(order=i, narration=t, image_prompt=images.extract_keywords(t, 5) or t)
                     for i, t in enumerate(sentences)]
        s.add(st)
        s.commit()
        print(f"created story {st.id} with {len(st.scenes)} scenes")


def cmd_render(a):
    h = worker.WorkerHandle(paths.data_dir())
    h.start()
    job = h.submit("render_story", story_id=a.story_id)
    t0 = time.time()
    try:
        while True:
            for ev in h.events():
                stamp = f"[{time.time() - t0:6.1f}s]"
                if ev["type"] == "stage":
                    info = " ".join(f"{k}={v}" for k, v in ev.get("info", {}).items() if k != "url")
                    print(f"{stamp} scene {ev['scene_id']:>3} {ev['stage']:<5} {ev['status']:<7} {info}")
                elif ev["type"] == "job_done" and ev["job_id"] == job:
                    return
                else:
                    print(f"{stamp} {ev.get('type')} {ev.get('status', '')} {ev.get('error', '')}".rstrip())
            if not h.is_alive():
                print("worker died", file=sys.stderr)
                sys.exit(1)
            time.sleep(0.2)
    finally:
        h.stop()
        cmd_show(a)


def cmd_show(a):
    with db.Session() as s:
        st = s.get(db.Story, a.story_id)
        print(f"\nStory {st.id} '{st.title}' [{st.status}] {st.error or ''}\nfinal: {st.final_path}")
        print(f"{'#':>3} {'image':<7} {'source':<14} {'voice':<7} {'engine':<11} {'dur':>5} {'clip':<7} narration")
        for sc in st.scenes:
            print(f"{sc.order:>3} {sc.image_status:<7} {sc.image_source or '':<14} {sc.voice_status:<7} "
                  f"{sc.voice_engine or '':<11} {sc.duration_s or 0:5.1f} {sc.clip_status:<7} {sc.narration[:40]}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="desktop.cli")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("import-laravel").set_defaults(fn=cmd_import)
    c = sub.add_parser("create")
    c.add_argument("--title", required=True)
    c.add_argument("--text", required=True)
    c.add_argument("--aspect", default="16:9", choices=["16:9", "9:16"])
    c.add_argument("--style", default="story")
    c.set_defaults(fn=cmd_create)
    for name, fn in (("render", cmd_render), ("show", cmd_show)):
        x = sub.add_parser(name)
        x.add_argument("story_id", type=int)
        x.set_defaults(fn=fn)
    a = p.parse_args(argv)
    _boot()
    a.fn(a)


if __name__ == "__main__":
    main()
