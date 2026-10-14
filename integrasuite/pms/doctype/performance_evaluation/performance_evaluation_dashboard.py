from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'transactions': [
			{
				'label': _('Target and Review'),
				'items': ['Target Set Up','Review']
			}
		]
	}
