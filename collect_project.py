import argparse
import os
from pathlib import Path
# python collect_project.py . all_project.txt

# Папки, которые обычно не нужны в дампе проекта
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".next",
    ".nuxt",
    ".cache",
    ".pytest_cache",
    ".mypy_cache",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "dist",
    "build",
    "out",
    "target",
    "coverage",
    ".gradle",
    ".mvn",
}

# Расширения, которые обычно являются бинарными или тяжелыми
IGNORE_SUFFIXES = {
    # Изображения
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".bmp",
    ".tiff",
    ".svgz",

    # Шрифты
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",

    # Архивы
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".jar",
    ".war",

    # Бинарники/скомпилированные файлы
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".pyc",
    ".pyo",
    ".class",
    ".o",
    ".obj",
    ".wasm",

    # Медиа
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".wav",
    ".flac",

    # Базы данных и другое
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pdf",
}

# Файлы, которые лучше не включать, чтобы случайно не включить секреты
IGNORE_FILES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    "id_rsa",
    "id_ed25519",
    ".npmrc",
    ".pypirc",
}


def should_skip_dir(name: str, include_hidden: bool) -> bool:
    if name in IGNORE_DIRS:
        return True

    if name.startswith(".") and not include_hidden:
        return True

    return False


def is_probably_binary(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
            return b"\0" in chunk
    except OSError:
        return True


def read_text_file(path: Path):
    if is_probably_binary(path):
        return None

    # Сначала пробуем UTF-8, потом Windows-1251 на случай кириллицы
    for encoding in ("utf-8", "cp1251"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError as e:
            return f"[ERROR] Не удалось прочитать файл: {e}"

    # Если кодировка не определилась, читаем с заменой символов
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text + "\n[WARNING] Файл прочитан с заменой символов. Возможна нестандартная кодировка."
    except OSError as e:
        return f"[ERROR] Не удалось прочитать файл: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Собирает текстовые файлы проекта в один файл."
    )

    parser.add_argument(
        "source",
        help="Папка проекта, например: . или C:/projects/my_project",
    )

    parser.add_argument(
        "output",
        help="Файл, куда всё записать, например: all_project.txt",
    )

    parser.add_argument(
        "--max-size",
        type=int,
        default=2_000_000,
        help="Максимальный размер одного файла в байтах. По умолчанию 2 MB.",
    )

    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Не пропускать скрытые файлы и папки, начинающиеся с точки.",
    )

    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()

    if not source.is_dir():
        raise SystemExit(f"Папка проекта не найдена: {source}")

    files = []

    for root, dirs, names in os.walk(source):
        root_path = Path(root)

        # Сортируем папки, чтобы порядок был предсказуемым
        dirs[:] = sorted(
            d for d in dirs if not should_skip_dir(d, args.include_hidden)
        )

        for name in sorted(names):
            path = root_path / name

            try:
                resolved_path = path.resolve()
            except OSError:
                continue

            # Пропускаем сам итоговый файл, если он лежит внутри проекта
            if resolved_path == output:
                continue

            # Пропускаем скрытые файлы, если не указан --include-hidden
            if not args.include_hidden and name.startswith("."):
                continue

            # Пропускаем потенциально секретные файлы
            if name in IGNORE_FILES:
                continue

            # Пропускаем нежелательные расширения
            if path.suffix.lower() in IGNORE_SUFFIXES:
                continue

            if path.is_file():
                files.append(path)

    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as out:
        out.write(f"PROJECT DUMP: {source}\n")

        for path in files:
            relative_path = path.relative_to(source).as_posix()

            out.write("\n\n")
            out.write("=" * 20)
            out.write(f" FILE: {relative_path} ")
            out.write("=" * 20)
            out.write("\n")

            try:
                size = path.stat().st_size
            except OSError as e:
                out.write(f"[ERROR] Не удалось получить информацию о файле: {e}\n")
                continue

            if size > args.max_size:
                out.write(
                    f"[SKIPPED] Файл больше лимита: {size} байт. "
                    f"Лимит: {args.max_size} байт.\n"
                )
                continue

            content = read_text_file(path)

            if content is None:
                out.write("[SKIPPED] Похоже, это двоичный файл.\n")
            else:
                out.write(content.rstrip())
                out.write("\n")

    print(f"Готово: {output}")
    print(f"Файлов обработано: {len(files)}")


if __name__ == "__main__":
    main()