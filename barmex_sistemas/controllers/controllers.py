# -*- coding: utf-8 -*-
# from odoo import http


# class Sistemas(http.Controller):
#     @http.route('/sistemas/sistemas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sistemas/sistemas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sistemas.listing', {
#             'root': '/sistemas/sistemas',
#             'objects': http.request.env['sistemas.sistemas'].search([]),
#         })

#     @http.route('/sistemas/sistemas/objects/<model("sistemas.sistemas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sistemas.object', {
#             'object': obj
#         })
