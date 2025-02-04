from g4f.client import Client


def read_pgn_file(file_path):
    with open(file_path, 'r') as file:
        pgn_content = file.read()
    return pgn_content


def read_promt_file(file_path):
    with open(file_path, 'r') as file:
        promt_content = file.read()
    return promt_content


def send_to_chatgpt_api(pgn, promt):
    client = Client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": promt+pgn}],
        web_search=False
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    pgn = read_pgn_file(
        input('Enter file name located in this dir:\n') + '.pgn')
    promt = read_pgn_file('promt.txt')

    print(send_to_chatgpt_api(pgn, promt))
