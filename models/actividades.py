# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class Actividades (models.Model):
    _name = 'actividades'

    name = fields.Char('name')
    company_id = fields.Many2one('res.company',string='Company', store=True, readonly=True,default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned to', store=True, readonly=False,default=lambda self: self.env.user and self.env.user.id or False )
    ticket = fields.Char('ticket')
    partner_id = fields.Many2one('res.partner', string='partner')
    case_id = fields.Many2one('helpdesk.ticket', string='Caso')
    project_id = fields.Many2one('project.project', string='Proyecto')
    task_id = fields.Many2one('project.task', string='Tarea')
    descripcion = fields.Html('descripcion')    
    cliente = fields.Boolean('cliente')
    fecha_vencimiento = fields.Date('fecha_vencimiento')
    state = fields.Selection([
        ('0', 'Borrador'),
        ('1', 'Pendiente'),
        ('2', 'En curso'),
        ('3', 'Finalizado')
    ],default='0' ,string='Estado')