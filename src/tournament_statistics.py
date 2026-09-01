from Tournament import Tournament


def main():
    tournament = Tournament()
    tournament.run_tournament(num_games=10)
    print(f"Wrote tournament statistics to {tournament.report_path}")


if __name__ == "__main__":
    main()
