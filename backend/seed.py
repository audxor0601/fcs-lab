"""data 폴더의 shots CSV 를 한 번에 DB 에 넣는다.

Swagger 에서 아홉 번 반복하는 대신 이걸 실행한다.
이미 들어간 파일은 건너뛰므로 여러 번 실행해도 중복되지 않는다.

    python seed.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app import models  # noqa: E402
from app.csv_parser import CsvFormatError, parse_shots_csv  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402

DATA_DIR = Path(__file__).parent.parent / "data"


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        print(f"[!] {DATA_DIR} 에 CSV 가 없습니다.")
        return

    added = skipped = failed = 0
    for path in files:
        exists = (
            db.query(models.Experiment)
            .filter(models.Experiment.source_filename == path.name)
            .first()
        )
        if exists:
            print(f"  건너뜀  {path.name} (이미 등록됨)")
            skipped += 1
            continue

        try:
            meta, records = parse_shots_csv(path.read_bytes(), path.name)
        except CsvFormatError as e:
            print(f"  실패    {path.name} — {e}")
            failed += 1
            continue

        run_no = meta["run_no"]
        exp = models.Experiment(
            name=f"{run_no}회차" if run_no else path.stem,
            note="",
            **meta,
        )
        db.add(exp)
        db.flush()
        db.add_all([models.Shot(experiment_id=exp.id, **r) for r in records])
        db.commit()

        print(f"  등록    {path.name}  ({meta['shot_count']}발)")
        added += 1

    db.close()
    print(f"\n등록 {added} / 건너뜀 {skipped} / 실패 {failed}")


if __name__ == "__main__":
    main()
