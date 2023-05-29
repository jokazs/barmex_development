odoo.define('sh_all_in_one_disable_followers.Followers', function (require) {
"use strict";


	var AbstractField = require('web.AbstractField');
	var concurrency = require('web.concurrency');
	var core = require('web.core');
	var Dialog = require('web.Dialog');
	var field_registry = require('web.field_registry');
	var Followers = require('mail.Followers');
	
	var _t = core._t;
	var QWeb = core.qweb;
	
	Followers.include({
		_inviteFollower: function (channel_only) {
	        var action = {
	            type: 'ir.actions.act_window',
	            res_model: 'mail.wizard.invite',
	            view_mode: 'form',
	            views: [[false, 'form']],
	            name: _t("Invite Follower"),
	            target: 'new',
	            context: {
	                'default_res_model': this.model,
	                'default_res_id': this.res_id,
	                'mail_invite_follower_channel_only': channel_only,
	                'manually_added_follower':true
	            },
	        };
	        this.do_action(action, {
	            on_close: this._reload.bind(this),
	        });
	    },
	    
	    _follow: function () {
	        var kwargs = {
	            partner_ids: [this.partnerID],
	            context: {  'manually_added_follower':true}, // FIXME
	        };
	        this._rpc({
	                model: this.model,
	                method: 'message_subscribe',
	                args: [[this.res_id]],
	                kwargs: kwargs,
	            })
	            .then(this._reload.bind(this));
	    },
	});
	
});