from pathlib import Path
import argparse


def remove_kort_suffix(folder_path):
	folder = Path(folder_path)

	if not folder.exists():
		print(f"Folder does not exist: {folder}")
		return

	for file in folder.iterdir():
		if file.is_file() and file.stem.endswith("_kort"):
			new_name = file.stem[:-5] + file.suffix
			new_path = file.with_name(new_name)

			print(f"Renaming: {file.name} -> {new_path.name}")
			file.rename(new_path)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(
		description="Remove '_kort' from filenames in a folder."
	)
	parser.add_argument(
		"path",
		help="Path to the folder containing the files"
	)

	args = parser.parse_args()

	remove_kort_suffix(args.path)