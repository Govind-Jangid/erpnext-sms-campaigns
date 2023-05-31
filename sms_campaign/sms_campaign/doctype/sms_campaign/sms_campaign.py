# Copyright (c) 2023, Finesoft Afrika and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.safe_exec import get_safe_globals
from frappe.core.doctype.sms_settings.sms_settings import send_sms

class SMSCampaign(Document):
	
	def before_insert(self):
		query_params  = frappe.get_doc("SMS Campaign Query", self.query).params
		self.params = []
		for param in query_params:
			self.append("params", {
				"label": param.label,
				"value": param.value
			})
	
	def send_non_triggered_sms(self):
		parameters = {}
		for param in self.params:
			parameters[param.label] = param.value
		self.send_sms(parameters)

	def update_next_run_date(self):
		self.last_run_date = frappe.utils.nowdate()

		match self.repeats:
			case "Daily":
				self.next_run_date = frappe.utils.add_days(self.last_run_date, self.repeats_every)
			case "Weekly":
				self.next_run_date = frappe.utils.add_days(self.last_run_date, self.repeats_every * 7)	
			case "Monthly":
				self.next_run_date = frappe.utils.add_months(self.last_run_date, self.repeats_every)
			case "Yearly":
				self.next_run_date = frappe.utils.add_months(self.last_run_date, self.repeats_every * 12)

	
	def send_triggered_sms(self, doc_name):
		parameters = {}
		parameters[frappe.db.get_value("SMS Campaign Query", self.query, "doc_name_field")] = doc_name
		for param in self.params:
			parameters[param.label] = param.value
		self.send_sms(parameters)

	def on_submit(self):
		if self.trigger_type == "DIRECT":
			self.send_non_triggered_sms()
		
		if self.trigger_type == "SCHEDULED":
			self.next_run_date = self.start_date
			
		self.save()

	def send_sms(self, parameters):
		query = frappe.get_doc("SMS Campaign Query", self.query)
		data = frappe.db.sql(query.query, parameters, as_dict=True)
		for row in data:
			phone = row[query.phone_field]
			msg=frappe.render_template(self.message, get_context(row))
			print("phone: ") 
			print(phone)
			print("message: " + msg)

			# if phone:
			# 	send_sms(receiver_list = phone, msg = msg)
			# send_sms(receiver_list = phone, msg = msg)
						


def get_context(data):
	data["nowdate"] = frappe.utils.nowdate
	data["frappe"] = frappe._dict(utils=get_safe_globals().get("frappe").get("utils"))

	return data
	
def send_sheduled_sms():
	sms_campaigns = frappe.get_all("SMS Campaign", filters={"trigger_type": "SCHEDULED", "docstatus": 1, "active":1, "next_run_date": frappe.utils.nowdate()})
	for sms_campaign in sms_campaigns:
		sms_campaign = frappe.get_doc("SMS Campaign", sms_campaign.name)
		sms_campaign.send_non_triggered_sms()
		sms_campaign.update_next_run_date()
		sms_campaign.save()
		frappe.db.commit()

def send_triggered_after_insert_sms(doc, method=None):
	sms_campaigns = frappe.get_all("SMS Campaign", filters={"trigger_type": "TRIGGERED", "docstatus": 1, "active":1, "trigger": "New", "trigger_doctype": doc.doctype})
	for sms_campaign in sms_campaigns:
		sms_campaign = frappe.get_doc("SMS Campaign", sms_campaign.name)
		sms_campaign.send_triggered_sms(doc.name)
		sms_campaign.save()
		frappe.db.commit()

def send_triggered_on_submit_sms(doc, method=None):
	sms_campaigns = frappe.get_all("SMS Campaign", filters={"trigger_type": "TRIGGERED", "docstatus": 1, "active":1, "trigger": "Submit", "trigger_doctype": doc.doctype})
	for sms_campaign in sms_campaigns:
		sms_campaign = frappe.get_doc("SMS Campaign", sms_campaign.name)
		sms_campaign.send_triggered_sms(doc.name)
		sms_campaign.save()
		frappe.db.commit()

def send_triggered_on_cancel_sms(doc, method=None):
	sms_campaigns = frappe.get_all("SMS Campaign", filters={"trigger_type": "TRIGGERED", "docstatus": 1, "active":1, "trigger": "Cancel", "trigger_doctype": doc.doctype})
	for sms_campaign in sms_campaigns:
		sms_campaign = frappe.get_doc("SMS Campaign", sms_campaign.name)
		sms_campaign.send_triggered_sms(doc.name)
		sms_campaign.save()
		frappe.db.commit()

def send_triggered_on_update_sms(doc, method=None):
	sms_campaigns = frappe.get_all("SMS Campaign", filters={"trigger_type": "TRIGGERED", "docstatus": 1, "active":1, "trigger": "Save", "trigger_doctype": doc.doctype})
	for sms_campaign in sms_campaigns:
		sms_campaign = frappe.get_doc("SMS Campaign", sms_campaign.name)
		sms_campaign.send_triggered_sms(doc.name)
		sms_campaign.save()
		frappe.db.commit()