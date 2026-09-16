# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PMSUnfreeze(Document):
	def on_submit(self):
		self.update_pms()
  
	def update_pms(self):
		doc = frappe.get_doc(self.pms_to_unfreeze,self.unfreeze)
		doc.reference = self.name
		doc.reason = self.reason
		doc.save(ignore_permissions=True)
		# frappe.throw(str(doc.name))
		
     
