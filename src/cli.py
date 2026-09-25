import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

from src.pipeline import run_search
from src.scoring.classifier import classify_paper
from src.scoring.decision import decide_paper
from src.storage.csv_store import load_pool, save_pool


load_dotenv()

DEFAULT_CSV_PATH = Path("data/papers.csv")


def reclasificar(csv_path=DEFAULT_CSV_PATH) -> dict:
    """Recompute classification and decision for every non-reviewed paper, with no network calls."""
    papers = load_pool(csv_path)
    recalculados = 0
    protegidos = 0
    for paper in papers:
        if paper.get("revisado"):
            protegidos += 1
            continue
        paper.update(classify_paper(paper))
        paper.update(decide_paper(paper))
        recalculados += 1

    save_pool(papers, csv_path)
    counts = {"recalculados": recalculados, "protegidos": protegidos}
    print(f"Resumen: recalculados={counts['recalculados']}, protegidos={counts['protegidos']}")
    return counts


def buscar(
    query: str,
    year_from: int = 2021,
    year_to: int = 2026,
    limit: int = 20,
    csv_path=DEFAULT_CSV_PATH,
) -> dict:
    """Run the shared collection and persistence pipeline."""
    result = run_search(query, year_from, year_to, limit, csv_path)
    counts = result["upsert"]
    print(
        "Resumen: "
        f"nuevos={counts['nuevos']}, "
        f"actualizados={counts['actualizados']}, "
        f"protegidos={counts['protegidos']}"
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect and curate papers.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    buscar_parser = subparsers.add_parser("buscar", help="Search for papers.")
    buscar_parser.add_argument("query", help="Plain-text search query.")
    buscar_parser.add_argument("--year-from", type=int, default=2021)
    buscar_parser.add_argument("--year-to", type=int, default=2026)
    buscar_parser.add_argument("--limit", type=int, default=20)
    buscar_parser.add_argument("--csv-path", default=str(DEFAULT_CSV_PATH))

    reclasificar_parser = subparsers.add_parser(
        "reclasificar", help="Recompute classification and decision for non-reviewed papers."
    )
    reclasificar_parser.add_argument("--csv-path", default=str(DEFAULT_CSV_PATH))
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "buscar":
        buscar(
            args.query,
            year_from=args.year_from,
            year_to=args.year_to,
            limit=args.limit,
            csv_path=args.csv_path,
        )
    elif args.command == "reclasificar":
        reclasificar(csv_path=args.csv_path)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())