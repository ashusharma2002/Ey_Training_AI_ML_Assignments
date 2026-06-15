def save_markdown_report(
        file_path,
        content
):

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(content)