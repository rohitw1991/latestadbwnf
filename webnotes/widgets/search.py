# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
# MIT License. See license.txt 

# Search
from __future__ import unicode_literals
import webnotes
import webnotes.widgets.reportview
import webnotes.widgets.query_builder
from webnotes.utils import cstr

try:
	from startup.query_handlers import standard_queries
	startup_standard_queries = True
except ImportError:
	startup_standard_queries = False

# this is called by the Link Field
@webnotes.whitelist()
def search_link(doctype, txt, query=None, filters=None):
	search_widget(doctype, txt, query, page_len=20, filters=filters)
	webnotes.response['results'] = build_for_autosuggest(webnotes.response["values"])

# this is called by the search box
@webnotes.whitelist()
def search_widget(doctype, txt, query=None, searchfield="name", start=0, 
	page_len=50, filters=None):
	if isinstance(filters, basestring):
		import json
		filters = json.loads(filters)

	meta = webnotes.get_doctype(doctype)
	
	if query and query.split()[0].lower()!="select":
		# by method
		webnotes.response["values"] = webnotes.get_method(query)(doctype, txt, 
			searchfield, start, page_len, filters)
	elif startup_standard_queries and not query and doctype in standard_queries:
		# from standard queries
		search_widget(doctype, txt, standard_queries[doctype], 
			searchfield, start, page_len, filters)
	else:
		if query:
			# custom query
			webnotes.response["values"] = webnotes.conn.sql(scrub_custom_query(query, 
				searchfield, txt))
		else:
			if isinstance(filters, dict):
				filters_items = filters.items()
				filters = []
				for f in filters_items:
					if isinstance(f[1], (list, tuple)):
						filters.append([doctype, f[0], f[1][0], f[1][1]])
					else:
						filters.append([doctype, f[0], "=", f[1]])

			if filters==None:
				filters = []
			
			# build from doctype
			if txt:
				filters.append([doctype, searchfield or "name", "like", txt + "%"])
			if meta.get({"parent":doctype, "fieldname":"enabled", "fieldtype":"Check"}):
				filters.append([doctype, "enabled", "=", 1])
			if meta.get({"parent":doctype, "fieldname":"disabled", "fieldtype":"Check"}):
				filters.append([doctype, "disabled", "!=", 1])

			webnotes.response["values"] = webnotes.widgets.reportview.execute(doctype,
				filters=filters, fields = get_std_fields_list(meta, searchfield or "name"), 
				limit_start = start, limit_page_length=page_len, as_list=True)

def get_std_fields_list(meta, key):
	# get additional search fields
	sflist = meta[0].search_fields and meta[0].search_fields.split(",") or []
	sflist = ['name'] + sflist
	if not key in sflist:
		sflist = sflist + [key]

	return ['`tab%s`.`%s`' % (meta[0].name, f.strip()) for f in sflist]

def build_for_autosuggest(res):
	results = []
	for r in res:
		info = ''
		if len(r) > 1:
			info = ', '.join([cstr(t) for t in r[1:]])
			if len(info) > 50:
				info = "<span title=\"%s\">%s...</span>" % (info, info[:50])

		results.append({'label':r[0], 'value':r[0], 'info':info})
	return results

def scrub_custom_query(query, key, txt):
	if '%(key)s' in query:
		query = query.replace('%(key)s', key)
	if '%s' in query:
		query = query.replace('%s', ((txt or '') + '%'))
	return query
