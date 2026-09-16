from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'transactions': [
			{
				'label': _('Target Set Up and Performance Evaluation'),
				'items': ['Target Set Up', 'Performance Evaluation']
			}
		]
	}
