import pymupdf
import re
import os
from dataclasses import dataclass

@dataclass
class PdfInfo:
	file_path: str
	search_word: str
	art_nr: str | None = None
	serie_nummer: str | None = None
	to_nummer: str | None = None
	start_page: int | None = None
	end_page: int | None = None
	has_red_text: bool = False
	new_root_dir: str | None = None
	error: bool = False

def check_if_red_text_in_page(page):
	# Placeholder function to check for red text
	# Implement your logic here to detect red text on the page
	text_dict=page.get_text("dict")

	for block in text_dict["blocks"]:
		if "lines" in block:
			for line in block["lines"]:
				for span in line["spans"]:
					if span["color"] == 16711680:  # Number for red
						#print(f"Red text found: {span['text']}, Page number: {page.number}")
						return True	
	return False

def extract_pdf_info(doc, args) -> PdfInfo:
	info = PdfInfo(file_path=doc.name, search_word=args.search) 

	RELEVANT_PAGE_COUNT = None
	possible_end_pages = None
	looking_for_end_page = False
	# Iterate through pages
	for page in doc:
		
		text = page.get_text()
		lines = text.splitlines()
		search_word_found = False

		for line in lines:
			# Check for Art.nr.
			if info.art_nr is None and "Art.nr. :" in line:
				info.art_nr = line.split("Art.nr. :")[1].strip() # ger oftest denna ['', ' 5957732'] men finns iband mer text i slutet
				#print(f"Art.nr.: {info.art_nr}")
			
			# Check for SerieNummer
			if info.serie_nummer is None and "SerieNummer :" in line:
				info.serie_nummer = (line.split("SerieNummer :")[-1].strip()).split("#")[-1].strip()
				#print(f"SerieNummer: {info.serie_nummer}")
			
			# Check for To.nr.
			if info.to_nummer is None and "Order :" in line:
				info.to_nummer = line.split("Order :")[-1].strip()
				#print(f"To.nr.: {info.to_nummer}")

			if info.art_nr is not None and info.serie_nummer is not None and info.search_word is not None and info.start_page is None:
				if info.search_word.lower() in line.lower():
					info.start_page = page.number
					if page.number == doc.page_count - 1:
						looking_for_end_page = False
						info.end_page = page.number
					else:
						looking_for_end_page = True
					break

			elif info.art_nr is not None and info.serie_nummer is not None and info.start_page is None:
				# Find all possible end pages based on page numbers in the text, store in list.
				info.start_page = page.number
				#print(f"Found both Art.nr. and SerieNummer on page {info.start_page}")
				page_number_match = re.findall(r'\b(\d{1,3})/(\d{1,3})\b', text)
				#extract number after "/" in the page number match
				#print(page_number_match)
				if page_number_match:
					page_number_match = [int(match[-1]) for match in page_number_match]
					possible_end_pages = page_number_match
					if len(possible_end_pages) == 1:
						RELEVANT_PAGE_COUNT = possible_end_pages[0]
						info.end_page = info.start_page + RELEVANT_PAGE_COUNT - 1
						#print(f"Determined end page: {info.end_page} based on page number match: {page_number_match} on page {page.number}")
					else:
						print("ERROR: Multiple possible page numbers were found")
						print(f"Possible end page: {page.number} with page number matches: {page_number_match}")

				"""elif info.start_page is not None and info.end_page is None:
				# This is done if more than one possible end page is found on the start page.
				# Here we check for page numbers and if they don't match the possible end pages, we remove them from the list of possible end pages. If there is only one possible end page left, we set it as the end page.
				
				page_number_match = re.findall(r'\b(\d{1,3})/(\d{1,3})\b', text)
				#print(page_number_match)
				if page_number_match:

					for match in page_number_match:
						page_num = int(match[-1])
						#print (page_num)
						for possible_end_page in possible_end_pages:
							if page_num != possible_end_page:
								possible_end_pages.remove(possible_end_page)
								print(f"Removed possible end page: {possible_end_page} based on page number match: {page_num} on page {page.number}")
								
							if len(possible_end_pages) == 1:
								RELEVANT_PAGE_COUNT = possible_end_pages[0]
								info.end_page = info.start_page + RELEVANT_PAGE_COUNT - 1
								print(f"Determined end page: {info.end_page} based on remaining possible end pages: {possible_end_pages}")
								# break all loops
								break
					if info.end_page:
						break
				"""

				if looking_for_end_page:
					if info.search_word.lower() in line.lower():
						search_word_found = True
		
		if looking_for_end_page:
			if not search_word_found:
				info.end_page = page.number -1

		# if star.page not found also look for word
		if info.end_page:
			break
	
	if info.art_nr is not None and info.serie_nummer is not None and info.to_nummer is not None and info.start_page is not None and info.end_page is not None:
		info.error = False             
		print(f"Start page: {info.start_page}")
		print(f"End page: {info.end_page}")
	else:
		# write what information could not be found
		print(info.art_nr)
		info.error = True
		print("ERROR: Could not find information")
		if info.art_nr is None:
			print("Could not find Art.nr")
		if info.to_nummer is None:
			print("Could not find to_nummer")
		if info.serie_nummer is None:
			print("Could not find serienummer")
		if info.start_page is None:
			print("Could not find start page")
		if info.end_page is None:
			print("Could not find end page")
		
	return info

def process_pdf(file_path, args):

	# open file 
	doc = pymupdf.open(file_path)

	# Find information art.nr. and serie_nummer as well as the start page and end page of the relevant information.
	info = extract_pdf_info(doc, args)
	file_path_root = os.path.dirname(file_path)

	# See if red text is present in the relevant pages.
	if info.error:
		path_to_krasch = os.path.join(file_path_root, "krasch")
		os.makedirs(path_to_krasch, exist_ok=True)
		doc.save(os.path.join(path_to_krasch, os.path.basename(file_path))) # save the original document in the krasch folder
		print(f"Error processing file: {file_path}. Saving to krasch folder.")	
		doc.close()
		os.remove(file_path)
		return info
	
	# See if red text is present in the relevant pages.
	for page_num in range(info.start_page, info.end_page + 1):
		
		page = doc.load_page(page_num)
		
		if check_if_red_text_in_page(page):
			info.has_red_text = True
			#print(f"Red text found on page {page_num}")
			break

	# Create directories if they don't exist, with the name of the Art.nr. and subdirectories "Original", "Error", and "Correct".
	file_path_root = os.path.dirname(file_path)
	if info.art_nr:
		base_dir = os.path.join(file_path_root, info.art_nr)
		info.new_root_dir = base_dir
		sub_dirs = ["Original", "Error", "Correct"] # Subfolder names

		if not os.path.exists(base_dir):
			os.makedirs(base_dir)
			print(f"Directory created: {base_dir}")
		for sub_dir in sub_dirs:
			dir_path = os.path.join(base_dir, sub_dir)

			if not os.path.exists(dir_path):
				os.makedirs(dir_path)
				print(f"Directory created: {dir_path}")

	# Create new PDF with the pages of the original document in the range start_page to end_page 
	short_doc = pymupdf.open()  # Create a new PDF document
	short_doc.insert_pdf(doc, from_page=info.start_page, to_page=info.end_page)  # Insert pages from the original document

	# Save files in the correct folders depending on if red text is present or not, with appropriate names.
	# File name should be in the format "Art.nr. + TO_nr + _SerieNummer.pdf"

	file_name_base = info.art_nr + "_" + info.to_nummer + "#" + info.serie_nummer

	# Check if files with this name base already exists in the Original folder, if so, add a number at the end of the file name base to make it unique.
	file_dir_name = os.path.join(base_dir, "Original")

	same_base_files = [file for file in os.listdir(file_dir_name) if file.startswith(file_name_base) and (file.endswith(".pdf") or file.endswith(".PDF"))]
	
	if same_base_files:
		index  = len(same_base_files)
		file_name_base += f"_({index})"

	if info.has_red_text:
		file_name_long = os.path.join(base_dir, "Original", file_name_base + "_röd.pdf")
		file_name_short = os.path.join(base_dir, "Error", file_name_base + "_röd_kort.pdf")
	else:
		file_name_long = os.path.join(base_dir, "Original", file_name_base + ".pdf")
		file_name_short = os.path.join(base_dir, "Correct", file_name_base + ".pdf")
	
	doc.save(file_name_long) # save the original document with all pages in the Original folder
	short_doc.save(file_name_short) # save the new document with only the relevant pages in the Correct or Error folder depending on if red text is present or not
	doc.close()
	short_doc.close()
	os.remove(file_path) #remove file from start destination
	
	return info # return the info object for the Art.nr. to be used in the summary file

def write_summary_to_txt(base_dir, args):
	
	# Count number of files in each directory and write to summary file
	summary_file_path = os.path.join(base_dir, "summary.txt")
	summary_file = open(summary_file_path, "w")

	# First summary for the krasch folder, with the amount of files in the krasch folder.
	krasch_dir = os.path.join(os.path.dirname(base_dir), "krasch")
	if os.path.exists(krasch_dir):
		krasch_file_count = len([file for file in os.listdir(krasch_dir) if file.endswith(".pdf") or file.endswith(".PDF")])
		summary_file.write(f"Krasch: {krasch_file_count} files\n")
		print(f"Krasch: {krasch_file_count} files")
	else:
		summary_file.write("Krasch: 0 files\n")
		print("Krasch folder does not exist")

	#summary of the Original, Error and Correct folders with the amount of files in each folder.
	sub_dirs = ["Original", "Error", "Correct"]
	
	for sub_dir in sub_dirs:
		dir_path = os.path.join(base_dir, sub_dir)
		if os.path.exists(dir_path):
			file_count = len([file for file in os.listdir(dir_path) if file.endswith(".pdf") or file.endswith(".PDF")])
			summary_file.write(f"{sub_dir}: {file_count} files\n")
			print(f"{sub_dir}: {file_count} files")

	# Extract serienummer from filenames in "Original" dir and store in a list
	serienummer_list = []
	original_dir_path = os.path.join(base_dir, "Original")
	if os.path.exists(original_dir_path):
		for file in os.listdir(original_dir_path):
			if file.endswith(".pdf") or file.endswith(".PDF"):
				serienummer_match = re.search(r'#(\d+)', file)
				if serienummer_match:
					serienummer = int(serienummer_match.group(1))
					serienummer_list.append(serienummer)
	
	max_serie_nummer = max(serienummer_list) if serienummer_list else None
	summary_file.write(f"Max SerieNummer: {max_serie_nummer}\n")
	print(f"Max SerieNummer: {max_serie_nummer}")

	# Extract serinummer from files in "Correct" dir and store in a list
	correct_dir_path = os.path.join(base_dir, "Correct")
	correct_serienummer_list = []
	if os.path.exists(correct_dir_path):
		for file in os.listdir(correct_dir_path):
			if file.endswith(".pdf") or file.endswith(".PDF"):
				serienummer_match = re.search(r'#(\d+)', file)
				if serienummer_match:
					serienummer = int(serienummer_match.group(1))
					correct_serienummer_list.append(serienummer)
	
	# Check if all numbers from 1 to max_serie_nummer are present in the correct_serienummer_list, if not, write the missing numbers to the summary file.
	if max_serie_nummer is not None:
		existing_serienummer = set()

		if args.mätfrekvens is not None:
			existing_serienummer.update(
				range(0, max_serie_nummer + 1, args.mätfrekvens)
			)
			existing_serienummer.add(1)

		if args.add_serienummer is not None:
			existing_serienummer.update(args.add_serienummer)

		if args.mätfrekvens is None and args.add_serienummer is None:
			existing_serienummer.update(
				range(1, max_serie_nummer + 1)
			)

		missing_serienummer = [
			num for num in existing_serienummer
			if num not in correct_serienummer_list
		]

		summary_file.write(f"Missing SerieNummer in Correct folder: "
					 f"{', '.join(f'{num:04d}' for num in missing_serienummer)}\n")
		summary_file.write(f"Number of missing SerieNummer: {len(missing_serienummer)}\n")
	
	from collections import Counter

	counter = Counter(correct_serienummer_list)
	
	duplicates = { num: count for num, count in counter.items() if count > 1}
	
	if duplicates:
		summary_file.write("Duplicate SerieNummer in Correct folder:\n")
		for num, count in sorted(duplicates.items()):
			summary_file.write(f"  {num:04d}: {count} occurrences\n")

	summary_file.close()
	
def __main__():
	# read the path to the folder with pdfs using parser
	import argparse
	import os
	parser = argparse.ArgumentParser(description="Process PDF files in a folder.")
	parser.add_argument("folder_path", type=str, help="Path to the folder containing PDF files")
	parser.add_argument("-s", "--search", type=str, help="Search word to find relevant pages if page count not availible")
	parser.add_argument("-m", "--mätfrekvens", type=int, help="Mätfrekvens för att veta relevanta serienummer")
	parser.add_argument("-a", "--add_serienummer", nargs = "+",  type=int, help="Om du vill lägga till mätpunkt som inte följer mätfrekvensen")
	args = parser.parse_args()
	path = args.folder_path	

	# Iterate through all PDF files in the folder
	for file_name in os.listdir(path):
		if file_name.endswith(".pdf") or file_name.endswith(".PDF"):
			file_path = os.path.join(path, file_name)
			print(f"Processing file: {file_path}")
			# Call the function to process the PDF file
			info = process_pdf(file_path, args)
			if not info.error:
				base_dir = info.new_root_dir
			
	
	#subfolder summary in Artn.nr. dir with a text file witht he amount of files in each subfolder
	write_summary_to_txt(base_dir, args)


if __name__ == "__main__":
	__main__()
