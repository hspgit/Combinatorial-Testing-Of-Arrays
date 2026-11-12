"""Command-line interface: ``cit-tools`` (or ``python -m cit_tools``).

Replaces the interactive prompts of the C++ programs with arguments, so the
tools can be scripted and batch-run::

    cit-tools report design.txt
    cit-tools coverage *.txt -t 2 3 --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from typing import Any

from cit_tools import __version__
from cit_tools._format import fmt, to_json_number
from cit_tools.design import Design, DesignError, interaction_label
from cit_tools.io import load_design
from cit_tools.metrics.chi_square import chi_square, chi_square_lower_bound, efficiency_from
from cit_tools.metrics.coverage import coverage
from cit_tools.metrics.saturation import degree_of_saturation
from cit_tools.report import build_report

__all__ = ["main"]

# A command turns (design, source, args) into (json-able dict, text block).
_Command = Callable[[Design, str, argparse.Namespace], tuple[dict[str, Any], str]]


def _saturation(
    design: Design, source: str, _args: argparse.Namespace
) -> tuple[dict[str, Any], str]:
    dos = degree_of_saturation(design)
    kind = "super-saturated" if dos > 1 else "not super-saturated"
    data = {
        "source": source,
        "degree_of_saturation": to_json_number(dos),
        "supersaturated": dos > 1,
    }
    return data, f"{source}: degree of saturation = {fmt(dos)} ({kind})\n"


def _header(design: Design, source: str) -> str:
    return f"{source} (N={design.num_rows}, k={design.num_columns})\n"


def _coverage(design: Design, source: str, args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    results = [coverage(design, t) for t in args.strength]
    data = {
        "source": source,
        "rows": design.num_rows,
        "columns": design.num_columns,
        "coverage": [
            {
                "strength": r.strength,
                "covered": r.covered,
                "possible": r.possible,
                "ratio": to_json_number(r.ratio),
            }
            for r in results
        ],
    }
    text = _header(design, source) + "".join(
        f"  t={r.strength}: {r.covered} / {r.possible} covered, ratio {fmt(r.ratio)}\n"
        for r in results
    )
    return data, text


def _chi_square(
    design: Design, source: str, args: argparse.Namespace
) -> tuple[dict[str, Any], str]:
    entries: list[dict[str, Any]] = []
    text = _header(design, source)
    for t in args.strength:
        result = chi_square(design, t)
        entry: dict[str, Any] = {
            "strength": t,
            "total": to_json_number(result.total),
            "average": to_json_number(result.average),
            "min": to_json_number(result.minimum),
            "max": to_json_number(result.maximum),
        }
        text += (
            f"  t={t}: total {fmt(result.total)}, average {fmt(result.average)}, "
            f"min {fmt(result.minimum)}, max {fmt(result.maximum)}\n"
        )
        if t == 2 and design.num_rows >= 2:
            bound = chi_square_lower_bound(design)
            efficiency = efficiency_from(bound, result.total)
            entry["lower_bound"] = to_json_number(bound)
            entry["efficiency"] = to_json_number(efficiency)
            text += f"        lower bound {fmt(bound)}, efficiency {fmt(efficiency)}\n"
        if args.values:
            entry["values"] = {
                interaction_label(cols): to_json_number(v) for cols, v in result.values.items()
            }
            width = max(len(interaction_label(cols)) for cols in result.values)
            text += "".join(
                f"        {interaction_label(cols).ljust(width)}  {fmt(v)}\n"
                for cols, v in result.values.items()
            )
        entries.append(entry)
    data = {
        "source": source,
        "rows": design.num_rows,
        "columns": design.num_columns,
        "chi_square": entries,
    }
    return data, text


def _report(design: Design, source: str, args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    report = build_report(design, source=source, coverage_strengths=args.strength)
    return report.to_dict(), report.format_text()


def _positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer: {text!r}") from None
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {value}")
    return value


class _LevelsAction(argparse.Action):
    """Parse --levels into a tuple of positive integers, accepting spaces or commas."""

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        if values is None:
            setattr(namespace, self.dest, None)
            return
        raw_items: list[str] = [values] if isinstance(values, str) else [str(v) for v in values]
        levels: list[int] = []
        for item in raw_items:
            for part in item.replace(",", " ").split():
                try:
                    val = int(part)
                    if val < 1:
                        raise ValueError
                except ValueError:
                    parser.error(f"argument --levels: invalid positive integer: {part!r}")
                levels.append(val)
        if not levels:
            parser.error("argument --levels: at least one level must be specified")
        setattr(namespace, self.dest, tuple(levels))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cit-tools",
        description="Quality metrics for combinatorial test designs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("files", nargs="+", metavar="FILE", help="design file(s)")
    common.add_argument(
        "--format", choices=["text", "json"], default="text", help="output format (default: text)"
    )
    common.add_argument("-o", "--output", metavar="PATH", help="write to PATH instead of stdout")
    common.add_argument(
        "--levels",
        action=_LevelsAction,
        default=None,
        metavar="L",
        help="explicit level count for each column (overrides inferred levels)",
    )
    common.add_argument(
        "--header",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="whether input CSV/TSV has a header row (default: auto-detect)",
    )

    def strength_arg(p: argparse.ArgumentParser, default: list[int] | None, help_: str) -> None:
        p.add_argument(
            "-t",
            "--strength",
            type=_positive_int,
            nargs="+",
            default=default,
            metavar="T",
            help=help_,
        )

    p = sub.add_parser("saturation", parents=[common], help="degree of saturation")
    p.set_defaults(handler=_saturation)

    p = sub.add_parser("coverage", parents=[common], help="t-way combination coverage")
    strength_arg(p, [2], "interaction strength(s) (default: 2)")
    p.set_defaults(handler=_coverage)

    p = sub.add_parser("chi-square", parents=[common], help="chi-square balance (and efficiency)")
    strength_arg(p, [2], "interaction strength(s) (default: 2)")
    p.add_argument("--values", action="store_true", help="list the value of every combination")
    p.set_defaults(handler=_chi_square)

    p = sub.add_parser("report", parents=[common], help="all metrics (like chi^2_efficiency.cpp)")
    strength_arg(p, None, "coverage strength(s) (default: 2 and 3, where defined)")
    p.set_defaults(handler=_report)
    return parser


def _normalize_argv(argv: Sequence[str] | None) -> list[str] | None:
    if argv is None:
        return None
    raw = list(argv)
    res: list[str] = []
    i = 0
    while i < len(raw):
        arg = raw[i]
        if arg == "--levels":
            i += 1
            levels: list[str] = []
            while i < len(raw) and not raw[i].startswith("-"):
                parts = raw[i].replace(",", " ").split()
                if parts and all(p.isdigit() and int(p) >= 1 for p in parts):
                    levels.extend(parts)
                    i += 1
                else:
                    break
            if levels:
                res.extend([arg, ",".join(levels)])
            elif i < len(raw) and not raw[i].startswith("-"):
                res.extend([arg, raw[i]])
                i += 1
            else:
                res.append(arg)
        else:
            res.append(arg)
            i += 1
    return res


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI; returns the process exit status (0 ok, 1 error, 2 usage)."""
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    args = _build_parser().parse_args(_normalize_argv(raw_argv))
    handler: _Command = args.handler
    results: list[tuple[dict[str, Any], str]] = []
    try:
        for path in args.files:
            design = load_design(path, levels=args.levels, header=args.header)
            results.append(handler(design, path, args))
    except (DesignError, OSError) as exc:
        print(f"cit-tools: error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        payload: Any = results[0][0] if len(results) == 1 else [data for data, _ in results]
        output = json.dumps(payload, indent=2) + "\n"
    else:
        output = "\n".join(text for _, text in results)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(output)
        except OSError as exc:
            print(f"cit-tools: error: {exc}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(output)
    return 0
