# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
# MIT License. See license.txt 

from __future__ import unicode_literals
import webnotes
import webnotes.model.doc
import webnotes.model.code

conn = webnotes.conn

@webnotes.whitelist()
def get(name):
	"""
	   Return the :term:`doclist` of the `Page` specified by `name`
	"""
	page = webnotes.bean("Page", name)
	page.run_method("get_from_files")
	return page.doclist

@webnotes.whitelist(allow_guest=True)
def getpage():
	"""
	   Load the page from `webnotes.form` and send it via `webnotes.response`
	"""
	page = webnotes.form_dict.get('name')
	doclist = get(page)
	
	if has_permission(doclist):
		# load translations
		if webnotes.lang != "en":
			from webnotes.modules import get_doc_path
			from webnotes.translate import get_lang_data
			d = doclist[0]
			messages = get_lang_data(get_doc_path(d.module, d.doctype, d.name), 
				webnotes.lang, 'js')
			webnotes.response["__messages"] = messages
				
		webnotes.response['docs'] = doclist
	else:
		webnotes.response['403'] = 1
		raise webnotes.PermissionError, 'No read permission for Page %s' % \
			(doclist[0].title or page, )
		
def has_permission(page_doclist):
	if webnotes.user.name == "Administrator" or "System Manager" in webnotes.user.get_roles():
		return True
		
	page_roles = [d.role for d in page_doclist if d.fields.get("doctype")=="Page Role"]
	if webnotes.user.name == "Guest" and not (page_roles and "Guest" in page_roles):
		return False
	
	elif page_roles and not (set(page_roles) & set(webnotes.user.get_roles())):
		return False

	return True