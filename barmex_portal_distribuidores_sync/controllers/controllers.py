# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerPortalSync(http.Controller):
#     @http.route('/customer_portal_sync/customer_portal_sync', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_portal_sync/customer_portal_sync/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_portal_sync.listing', {
#             'root': '/customer_portal_sync/customer_portal_sync',
#             'objects': http.request.env['customer_portal_sync.customer_portal_sync'].search([]),
#         })

#     @http.route('/customer_portal_sync/customer_portal_sync/objects/<model("customer_portal_sync.customer_portal_sync"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_portal_sync.object', {
#             'object': obj
#         })
