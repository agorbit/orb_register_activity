# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class Imputaciones (models.Model):
    _name = 'imputaciones'
    _description='Imputaciones de actividades'

    name = fields.Char('name')
    company_id = fields.Many2one('res.company',string='Company', store=True, readonly=True,default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned to', store=True, readonly=False,default=lambda self: self.env.user and self.env.user.id or False )
    ticket = fields.Char('ticket')
    partner_id = fields.Many2one('res.partner', string='partner')
    case_id = fields.Many2one('helpdesk.ticket', string='Caso')
    project_id = fields.Many2one('project.project', string='Proyecto')
    task_id = fields.Many2one('project.task', string='Tarea')
    fecha_inicio = fields.Datetime('fecha_inicio')
    fecha_final = fields.Datetime('fecha_final')
    tiempo = fields.Float('tiempo')
    factor = fields.Float('factor', default=1.00)
    tiempo_realizado = fields.Float('tiempo_realizado')
    tiempo_manual = fields.Float('tiempo_manual')
    tiempo_facturar = fields.Float('tiempo_facturar')
    descripcion = fields.Text('descripcion')
    state = fields.Selection([
        ('0', 'Borrador'),
        ('1', 'En curso'),
        ('2', 'Finalizado'),
        ('3', 'Imputado')
    ],default='0' ,string='Estado')


    #Botones

    def enprogreso(self):
        self.state = '1'
        self.fecha_inicio = datetime.today()

    def finalizar(self):
        self.state = '2'        
        self.fecha_final = datetime.today()
        FechaInicial = self.fecha_inicio
        FechaFinal = self.fecha_final
        diferencia = FechaFinal - FechaInicial
        self.tiempo = diferencia.total_seconds()/3600
        self.tiempo_realizado = self.tiempo * self.factor
        if self.tiempo_manual != 0:
            self.tiempo_facturar = self.tiempo_manual            
        else:
            self.tiempo_facturar = self.tiempo_realizado

    def imputado(self):
        self.state = '3'
    
    def recalcular(self):
        self.fecha_final = datetime.today()
        FechaInicial = self.fecha_inicio
        FechaFinal = self.fecha_final
        if FechaInicial != "" and FechaFinal != "":
            diferencia = FechaFinal - FechaInicial
            self.tiempo = diferencia.total_seconds()/3600
            self.tiempo_realizado = self.tiempo * self.factor
            if self.tiempo_manual != 0:
                self.tiempo_facturar = self.tiempo_manual            
            else:
                self.tiempo_facturar = self.tiempo_realizado
        
    
    #Cambios en campos

    @api.onchange('factor','tiempo_manual')
    def _on_change_factor(self):        
        self.recalcular() 


    @api.onchange('ticket')
    def _on_change_ticket(self):
        resultado = self.env['helpdesk.ticket'].search_count(['&',('id','=',int(self.ticket)),('partner_id','=',self.partner_id.id)])       
        if resultado > 0:
            casos = self.env['helpdesk.ticket'].search(['&',('id','=',int(self.ticket)),('partner_id','=',self.partner_id.id)])
            for caso in casos:
                self.case_id = caso.id
        else:
            self.case_id = ""
        
        
    
    #Crear registro en ticket
    
    def registro_ticket(self):
        resultado = self.env['helpdesk.ticket'].search_count([('id','=',int(self.ticket))])       
        if resultado > 0:
            casos = self.env['helpdesk.ticket'].search([('id','=',int(self.ticket))])  
            for caso in casos:                
                vals = {
                    'date':self.fecha_final,
                    'ticket_id': self.case_id,
                    'user_id': self.user_id,
                    'project_id': caso.project_id,
                    'unit_amount': self.tiempo_facturar 
                }
                
                self.env(['account.analytic.line']).create(vals)
        

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
    state = fields.Selection([
        ('0', 'Borrador'),
        ('1', 'Pendiente'),
        ('2', 'En curso'),
        ('3', 'Finalizado')
    ],default='0' ,string='Estado')