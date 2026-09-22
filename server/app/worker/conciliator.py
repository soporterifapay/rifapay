from ..db import SessionLocal
from ..services.matcher import run_matcher


def main():
    db = SessionLocal()
    try:
        matched = run_matcher(db)
        print(f"matched={matched}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
