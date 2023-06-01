from odoo import _, fields, models, _

class BarmexAlert(models.TransientModel):
    _name = "barmex.alert"
    _description = "Alert"

    partner_id = fields.Many2one('res.partner',
                                 readonly=True,
                                 string='Customer')

    exception_msg = fields.Text(readonly=True)

    origin_reference = fields.Reference(lambda self: [(m.model, m.name) for m in self.env["ir.model"].search([])],
                                        string="Ref Record")
    continue_method = fields.Char()

    def action_show(self, title):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def button_continue(self):
        self.ensure_one()
        return getattr(
            self.origin_reference.with_context(bypass_risk=True), self.continue_method
        )()