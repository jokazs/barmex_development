from odoo import models, fields, api, _

class Employee(models.Model):
    _inherit = 'hr.employee'

    lco_opportunity_ids = fields.Many2many('crm.lead',
                                           'crm_lead_hr_employee_rel',
                                           'hr_employee_id',
                                           'crm_lead_id',
                                           string='Opportunities')

    lco_ventas_mostrador = fields.Boolean('Check-in sale', track_visibility=True)

    #address_id = fields.Many2one('res.partner',
    #                             'Work Address',
    #                             domain="['|', ('parent_id', '=', address_filter), ('id', '=', address_filter)]")
    
    #address_id = fields.Many2one('res.partner', 'Work Address', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    #address_id = fields.Many2one('res.partner','Work Address',domain="['|',('type', '=', 'other'),('parent_id','=', address_filter)]")
    address_id = fields.Many2one('res.partner','Work Address')

    address_filter = fields.Integer(compute="set_filter")

    employee_sale_zone = fields.Many2one('barmex.sale.zone',
                                    string='Sale zone',
                                    stored=True,
                                    track_visibility=True,
                                    check_company=True)

    sequence = fields.Integer(default=1)

    work_phone = fields.Char('Teléfono de trabajo', compute="_compute_phones", store=True, readonly=False, track_visibility=True)
    work_email = fields.Char('Correo de trabajo', track_visibility=True)
    work_location = fields.Char('Ubicación de trabajo', track_visibility=True)
    department_id = fields.Many2one('hr.department', 'Departmento', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", track_visibility=True)
    job_id = fields.Many2one('hr.job', 'Puesto de Trabajo', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", track_visibility=True)
    parent_id = fields.Many2one('hr.employee', 'Responsable', store=True, readonly=False, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",track_visibility=True)

    x_studio_empleado_dado_de_baja = fields.Boolean('Empleado dado de baja', track_visibility=True)
    x_studio_rea = fields.Char('Área', track_visibility=True)
    x_studio_subrea = fields.Char('Subarea', track_visibility=True)
    x_studio_roles = fields.Char('Grupo de Acceso 1', track_visibility=True)
    x_studio_rol_2 = fields.Char('Grupo de Acceso 2', track_visibility=True)
    x_studio_corporativo = fields.Char('Corporativo', track_visibility=True)

    def set_filter(self):
        for record in self:
            record.update({
                'address_filter': self.env.company.partner_id.id,
            })

    @api.depends('address_id')
    def _compute_phones(self):
        for employee in self:
            if employee.address_id and employee.address_id.phone:
                employee.work_phone = employee.address_id.phone
            else:
                employee.work_phone = False


class EmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    lco_ventas_mostrador = fields.Boolean('Check-in sale')
