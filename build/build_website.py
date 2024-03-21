import os
import sys
import json
import re
from glob import glob
import pdb

ICONS = {"pdf": "fa-file-text-o",
		 "code": "fa-file-text-o",
		 "video": "fa-video-camera",
		 "powerpoint": "fa-file-powerpoint-o"}
DEFAULT_ICON = "fa-file-text-o"
DEFAULT_DOCUMENT = "<a <!--$$LINK$$-->><i class='fa fa <!--$$ICON$$--> text-primary'></i><span class='lecture-document'><!--$$NAME$$--></span></a></br>"
DEFAULT_RECORDING = "<a <!--$$LINK$$-->><i class='fa fa fa-video-camera text-primary'></i><span class='lecture-document'><!--$$NAME$$--></span></a></br>"
DEFAULT_TA_NAME = "<a href='<!--$$LINK$$-->' target='_blank' style='color: white;'><!--$$NAME$$--></a>"
DEFAULT_TA_PICTURE = "<a href='<!--$$LINK$$-->'><img class='img-circle' src='<!--$$IMAGE$$-->' hspace='5' width='120' alt='<!--$$NAME$$-->' title='<!--$$NAME$$-->'></a>"
DEFAULT_PICTURE_FILENAME = "images/people/default-picture.png"

def _create_document_list(document_dict):
	document_list = []
	for d in document_dict:
		doc_html = DEFAULT_DOCUMENT
		doc_html = doc_html.replace("<!--$$NAME$$-->", d["name"] + (" (link TBA)" if len(d["link"])==0 else ""))
		doc_html = doc_html.replace("<!--$$LINK$$-->", ("href='%s'"%d["link"]) if len(d["link"])>0 else "")
		doc_html = doc_html.replace("<!--$$ICON$$-->", ICONS.get(d["type"], DEFAULT_ICON))
		document_list.append(doc_html)
	document_list = "\n".join(document_list)
	if len(document_list) == 0:
		document_list = "No documents."
	return document_list

def _create_recording_list(recording_dict):
	recording_list = []
	for rec_num, record in enumerate(recording_dict):
		record_html = DEFAULT_RECORDING
		record["name"] = "Part %i: " % (rec_num+1) + record["name"]
		record_html = record_html.replace("<!--$$NAME$$-->", record["name"] + (" (link TBA)" if len(record["link"])==0 else ""))
		record_html = record_html.replace("<!--$$LINK$$-->", ("href='%s'"%record["link"]) if len(record["link"])>0 else "")
		recording_list.append(record_html)
	recording_list = "\n".join(recording_list)
	if len(recording_list) == 0:
		recording_list = "No recordings."
	return recording_list


def build_lectures(index_file,
				   json_filename="lectures.json",
				   lecture_template_filename="lecture_template.html"):

	with open(json_filename, "r") as f:
		lectures_dict = json.load(f)

	with open(lecture_template_filename, "r") as f:
		lecture_template = f.read()

	html_entries = []
	lecture_count = 0
	week = -1

	for idx, dict_entry in enumerate(lectures_dict):
		if week != dict_entry["week"]:
			html_entries.append('<p><h3>Week %i</h3></p>' % (dict_entry["week"]))
			week = dict_entry["week"]

		is_tutorial = (dict_entry["type"] == "tutorial")
		if is_tutorial:
			raise NotImplementedError("Tutorials are not yet supported.")
		else:
			lecture_count += 1
			entry_html = lecture_template
			dict_entry["name"] = "Lecture %i: " % (lecture_count) + dict_entry["name"]
			if idx < len(lectures_dict) - 1 and lectures_dict[idx+1]["week"] != week:
				dict_entry["style"] = "margin-bottom: 40px;"

		if "image" in dict_entry:
			assert os.path.isfile("../" + dict_entry["image"]), "Given image path \"%s\" does not point to an existing image." % dict_entry["image"]

		for tag, value in [("NAME", "name"), 
						   ("DATE", "date"),
						   ("DESCRIPTION", "desc"),
						   ("IMAGE", "image"),
						   ("STYLE", "style"),
						   ("LECTURER", "lecturer")]:
			if ("<!--$$%s$$-->" % tag) in entry_html:
				if not value in dict_entry:
					dict_entry[value] = ''
				entry_html = entry_html.replace("<!--$$%s$$-->" % tag, dict_entry[value])

		if "documents" in dict_entry:
			document_text = _create_document_list(dict_entry["documents"])
		else:
			document_text = "Documents will be added soon."
		entry_html = entry_html.replace("<!--$$DOCUMENTS$$-->", document_text)
		if not is_tutorial:
			if "recordings" in dict_entry:
				recordings_text = _create_recording_list(dict_entry["recordings"])
			else:
				recordings_text = "Recordings will be added soon."
			entry_html = entry_html.replace("<!--$$RECORDINGS$$-->", recordings_text)

		html_entries.append(entry_html)

	html_entries = "\n\n".join(html_entries)
	offset = re.findall(r" *<!--\$\$LECTURES\$\$-->", index_file)[0].split("<!--")[0]
	html_entries = html_entries.replace("\n", "\n" + offset)

	index_file = index_file.replace("<!--$$LECTURES$$-->", html_entries)

	return index_file


def build_TA_list(index_file,
				  json_filename="TAs.json"):
	
	with open(json_filename, "r") as f:
		TA_dict = json.load(f)

	TA_dict = sorted(TA_dict, key=lambda x : x["name"].split(" ")[-1])
	TA_dict = sorted(TA_dict, key=lambda x : x.get("type", None) is None)

	TA_name_list = []
	head_TA_name_list = []
	for TA in TA_dict:
		TA_name = DEFAULT_TA_NAME
		TA_name = TA_name.replace("<!--$$NAME$$-->", TA["name"])
		if "website" in TA and len(TA["website"]) > 0:
			TA["link"] = TA["website"]
		elif "mail" in TA and len(TA["mail"]) > 0:
			TA["link"] = "mailto:%s" % TA["mail"]
		else:
			# assert False, "Please provide at least a mail address for each TA."
			print('Warning: No link found for %s' % TA['name'])
			TA["link"] = ""
		TA_name = TA_name.replace("<!--$$LINK$$-->", TA["link"])
		if "type" in TA and TA["type"] == "Head TA":
			head_TA_name_list.append(TA_name)
		else:
			TA_name_list.append(TA_name)

	index_file = index_file.replace("<!--$$TA_NAMES$$-->", ", ".join(TA_name_list))

	TA_pic_list = []	
	for i, TA in enumerate(TA_dict):
		TA_pic = DEFAULT_TA_PICTURE
		TA_pic = TA_pic.replace("<!--$$NAME$$-->", TA["name"])
		if not "picture" in TA or len(TA["picture"]) == 0:
			search_str = '../images/people/' + TA['name'].lower().replace(' ','-') + '.jpg'
			pos_files = glob(search_str)
			if len(pos_files) == 0:
				TA['picture'] = ''
			else:
				TA['picture'] = pos_files[0]
		if len(TA["picture"]) == 0 or not (os.path.isfile(TA["picture"])):
			print("Warning: Could not find picture for %s. Using default picture..." % TA["name"])
			TA["picture"] = DEFAULT_PICTURE_FILENAME
		
		TA['picture'] = TA['picture'].replace('../','')
		TA_pic = TA_pic.replace("<!--$$IMAGE$$-->", TA["picture"])
		TA_pic = TA_pic.replace("<!--$$LINK$$-->", TA["link"])
		
		if (i + 1) % 4 == 0: # Every row should only have 4 pictures. First one is lecturer
			TA_pic = TA_pic + "</br></br>"
		TA_pic_list.append(TA_pic)
		

	index_file = index_file.replace("<!--$$TA_PICTURES$$-->", "\n".join(TA_pic_list))
	return index_file



if __name__ == '__main__':
	
	with open("index_template.html", "r") as f:
		index_file = f.read()

	index_file = build_TA_list(index_file)
	index_file = build_lectures(index_file)

	with open("../index.html", "w") as f:
		f.write(index_file)
