# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountInvoiceSend(models.TransientModel):
    _name = 'account.invoice.send'
    _inherits = {'mail.compose.message':'composer_id'}
    _description = 'Account Invoice Send'

    is_email = fields.Boolean('Email', default=lambda self: self.env.user.company_id.invoice_is_email)
    is_print = fields.Boolean('Print', default=lambda self: self.env.user.company_id.invoice_is_print)
    printed = fields.Boolean('Is Printed', default=False)
    invoice_ids = fields.Many2many('account.invoice', 'account_invoice_account_invoice_send_rel', string='Invoices')
    composer_id = fields.Many2one('mail.compose.message', string='Composer', required=True, ondelete='cascade')
    template_id = fields.Many2one(
        'mail.template', 'Use template', index=True,
        domain="[('model', '=', 'account.invoice')]"
        )

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoiceSend, self).default_get(fields)
        res_ids = self._context.get('active_ids')
        composer = self.env['mail.compose.message'].create({
            'composition_mode': 'comment' if len(res_ids) == 1 else 'mass_mail',
        })
        res.update({
            'invoice_ids': res_ids,
            'composer_id': composer.id,
        })
        return res

    @api.multi
    @api.onchange('invoice_ids')
    def _compute_composition_mode(self):
        for wizard in self:
            wizard.composition_mode = 'comment' if len(wizard.invoice_ids) == 1  else 'mass_mail'

    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.composer_id:
            self.composer_id.template_id = self.template_id.id
            self.composer_id.onchange_template_id_wrapper()

    @api.multi
    def _send_email(self):
        if self.is_email:
            self.composer_id.send_mail()

    @api.multi
    def _print_document(self):
        """ to override for each type of models that will use this composer."""
        self.ensure_one()
        action = self.invoice_ids.invoice_print()
        action.update({'close_on_report_download': True})
        return action

    @api.multi
    def send_and_print_action(self):
        self.ensure_one()
        self._send_email()
        if self.is_print:
            return self._print_document()
        return {'type': 'ir.actions.act_window_close'}
