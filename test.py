from chess_analysis import process_directory

prompt_file = "prompt2.txt"
pgn_directory = "pgns"


process_directory(
    pgn_dir=pgn_directory,
    prompt_file=prompt_file,
    model="deepseek-r1",
    verify=True,
    output_pgn_file="all_processed.pgn",
    output_segment_file="all_segments.txt"
)
