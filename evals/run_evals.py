import argparse
from opik import Opik
from tasks import all_tasks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", nargs="*", help="Run only specific tasks by experiment name")
    args = parser.parse_args()

    client = Opik()
    tasks_to_run = all_tasks
    if args.task:
        tasks_to_run = [t for t in all_tasks if t.experiment_name in args.task]

    for task in tasks_to_run:
        print(f"Running: {task.experiment_name}")
        task.run(client)


if __name__ == "__main__":
    main()
