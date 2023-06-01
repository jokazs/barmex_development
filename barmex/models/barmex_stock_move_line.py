from odoo import models, fields, api, _

class StockMove(models.Model):
    _inherit = ['stock.move.line']

    petition = fields.Char(string="Petition",
                           related="move_id.petition",
                           store=True)

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        #Asigna los pedimentos a los pedidos -- esta funcion hay que revisarla.
        if res.picking_id.picking_type_code == 'outgoing':
            demand = res.product_uom_qty
            pedimento = []
            stop = 3
            while demand > 0 or stop == 0:
                petition = res._get_move()
                print('Resultado domain')
                print(petition)
                if petition:
                    if petition.available < demand:
                        demand -= petition.available
                        petition.available = 0
                        if petition.historial:
                            petition.historial = petition.historial + f' [{res.picking_id.name}] - {petition.available}\r'
                        else:
                            petition.historial = f' [{res.picking_id.name}] - {petition.available}\r'
                    else:
                        petition.available -= demand
                        if petition.historial:
                            petition.historial = petition.historial + f' [{res.picking_id.name}] - {demand}\r'
                        else:
                            petition.historial = f' [{res.picking_id.name}] - {petition.available}\r'
                        demand = 0
                    if petition.petition:
                        pedimento.append(petition.petition)
                else:
                    demand = 0
                stop = stop -1
            if len(pedimento) > 0:
                try:
                    res.petition = ','.join(pedimento)
                except:
                    res.petition = ''
        return res

    def _get_move(self):
        domain = [('product_id', '=', self.product_id.id), ('available', '>', 0)]
        print(domain)
        if self.product_id.categ_id.removal_strategy_id.method == 'fifo':
            return self.env['barmex.petition.relation'].search(domain, order='date asc', limit=1)
        if self.product_id.categ_id.removal_strategy_id.method == 'lifo':
            return self.env['barmex.petition.relation'].search(domain, order='date desc', limit=1)