"""mcrogueface -m mcrf_project <command> ...   (see --help)"""
import argparse
import os
import sys
from pathlib import Path

from .errors import ProjectError
from .locate import locate
from .project import Project
from .runtime import Runtime, archive, copy_content, copy_release_docs, fresh_dir, web_archive


ENGINE_HELP = ("engine directory to use. Default: $MCROGUEFACE, then engine in mcrf.toml, "
               "then the newest ~/.local/share/mcrogueface/<version>/, then this engine")


def log(message):
    print("[mcrf] " + message, flush=True)


def cmd_init(args):
    project = Project(args.directory)
    log("project: %s" % project.dir)
    project.init(Runtime.running(), log)
    log("ready: cd %s, then `make run` or `%s -m mcrf_project run`"
        % (os.path.relpath(project.dir), sys.executable))


def cmd_run(args):
    project = Project(args.project)
    located = locate(project, flag=args.engine)
    log("engine: %s" % located.describe())
    return project.run(located.runtime, args.engine_args)


def cmd_dist(args):
    project = Project(args.project)
    out = Path(args.out) if args.out else project.dir / "dist"
    out.mkdir(parents=True, exist_ok=True)
    platforms = args.platform or [Runtime.running().platform]
    if args.engine and len(platforms) > 1:
        raise ProjectError("--engine names one engine; package one --platform at a time with it")
    for platform in platforms:
        if platform == "web":
            path = project.dist_web(Runtime.running(), out, log)
        else:
            located = locate(project, platform, flag=args.engine)
            log("engine: %s" % located.describe())
            path = project.dist(located.runtime, out, log)
        log("created %s" % path)


def cmd_info(args):
    project = Project(args.project)
    located = locate(project, flag=args.engine)
    engine = located.runtime
    if engine.is_running:
        import mcrfpy
        print("Engine:  McRogueFace %s (%s) at %s" % (mcrfpy.__version__, engine.title, engine.dir))
        print("Python:  %s" % sys.version.split()[0])
    else:
        print("Engine:  McRogueFace (%s) at %s" % (engine.title, engine.dir))
        print("Python:  %s" % engine.python_version)
    print("Chosen:  %s" % located.describe())
    if engine.source_root:
        print("Source:  %s" % engine.source_root)
    if (project.scripts / "game.py").is_file():
        print("Project: %s %s at %s" % (project.name, project.version, project.dir))
    else:
        print("Project: none at %s" % project.dir)


def cmd_package_engine(args):
    """The engine's own release package: its runtime, demo content and API docs."""
    engine = Runtime(args.engine) if args.engine else Runtime.running()
    name = "McRogueFace-%s-%s" % (args.version, engine.title)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    staged = fresh_dir(out / name)
    log("packaging %s from %s" % (name, engine.dir))
    engine.stage(staged)
    copy_content(staged,
                 engine.dir / "assets" if (engine.dir / "assets").is_dir() else None,
                 engine.dir / "scripts" if (engine.dir / "scripts").is_dir() else None)
    docs_root = Path(args.docs_from) if args.docs_from else engine.source_root
    if docs_root is None:
        raise ProjectError("no source tree to take the API docs from: pass --docs-from DIR")
    for missing in copy_release_docs(staged, docs_root):
        # Rendered docs are generated, not committed; say what didn't ship.
        log("WARNING: release doc missing, NOT bundled: %s "
            "(run tools/generate_all_docs.sh and regenerate the manifest)" % missing)
    log("created %s" % archive(staged, engine.platform))


def cmd_package_web(args):
    """The engine's own release web package, from a game-shell web build (make wasm-game)."""
    out = Path(args.out) / ("McRogueFace-%s-WASM.zip" % args.version)
    log("packaging %s from %s" % (out.name, Path(args.build).resolve()))
    log("created %s" % web_archive(args.build, out))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mcrogueface -m mcrf_project",
        description="Create, run and package McRogueFace games with this engine.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create a game project, or update an existing one")
    p.add_argument("directory", nargs="?", default=".", help="project directory (default: .)")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("run", help="run the game")
    p.add_argument("--project", default=".", help="project directory (default: .)")
    p.add_argument("--engine", help=ENGINE_HELP)
    p.add_argument("engine_args", nargs=argparse.REMAINDER,
                   help="arguments for the engine (after --), e.g. -- --headless")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("dist", help="package the game")
    p.add_argument("--project", default=".", help="project directory (default: .)")
    p.add_argument("--platform", action="append", choices=("linux", "windows", "web"),
                   help="repeatable; default: this engine's platform")
    p.add_argument("--engine", help=ENGINE_HELP)
    p.add_argument("--out", help="output directory (default: <project>/dist)")
    p.set_defaults(func=cmd_dist)

    p = sub.add_parser("info", help="show the engine and project, and why that engine")
    p.add_argument("--project", default=".", help="project directory (default: .)")
    p.add_argument("--engine", help=ENGINE_HELP)
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("package-engine", help="build an engine release package (tools/package.sh)")
    p.add_argument("--engine", help="engine directory (default: this engine)")
    p.add_argument("--version", required=True)
    p.add_argument("--out", required=True, help="output directory")
    p.add_argument("--docs-from", help="engine source tree holding the rendered docs "
                                       "(default: the engine's own)")
    p.set_defaults(func=cmd_package_engine)

    p = sub.add_parser("package-web", help="build the engine's release web zip from a web build")
    p.add_argument("--build", required=True, help="game-shell web build directory (build-wasm-game)")
    p.add_argument("--version", required=True)
    p.add_argument("--out", required=True, help="output directory")
    p.set_defaults(func=cmd_package_web)

    args = parser.parse_args(argv)
    if getattr(args, "engine_args", None) and args.engine_args[0] == "--":
        args.engine_args = args.engine_args[1:]
    try:
        return args.func(args) or 0
    except ProjectError as exc:
        print("mcrf_project: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
