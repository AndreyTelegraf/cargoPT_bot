from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = (
        PROJECT_ROOT / "app/bot/handlers/job_comment.py"
    ).read_text(encoding="utf-8")

    queued_assignment = "queued_count = result.queued_count"
    queued_branch = "elif queued_count > 0:"
    sent_branch = "elif sent_count > 0:"
    queued_message = "поставлена в очередь для подходящих перевозчиков"

    assert queued_assignment in source
    assert queued_branch in source
    assert sent_branch in source
    assert queued_message in source
    assert source.index(queued_branch) < source.index(sent_branch)
    assert "Мы отправили её подходящим перевозчикам: {queued_count}" not in source

    print("JOB_COMMENT_QUEUED_ACCEPTANCE_SMOKE_OK")


if __name__ == "__main__":
    main()
