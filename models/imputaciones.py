# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError


class Imputaciones (models.Model):
    _name = 'imputaciones'
    _description='Imputaciones de actividades'
    _inherit = 'mail.thread'
    

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
    account_analytic_line_id = fields.Many2one('account.analytic.line',string="Imputación analítica")
    where = fields.Char(compute='_compute_where', string='where')
    
    @api.depends('partner_id','project_id')
    def _compute_where(self):
        if self.partner_id.id != False:
            where = "('partner_id','=','" + str(self.partner_id.id) + ")"
            if self.project_id.id != False:
                where = "'&'," + where + "('project_id','=','" + str(self.project_id.id) + ")"                
        
        where = "[" + where + "]"


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
        if self.case_id.id == False and self.project_id.id == False:
            raise ValidationError("Caso o proyecto deben estar rellenados")
        else:
            if self.case_id.id == False and self.project_id.id != False and self.task_id.id == False:
                raise ValidationError("Si es una imputación de proyecto, proyecto y tarea debes estar rellenados")
            else:
                self.state = '3'
    
    def recalcular(self):
        if self.state != '0':
            self.fecha_final = datetime.today()
            FechaInicial = self.fecha_inicio
            FechaFinal = self.fecha_final
            if str(FechaInicial) != "False" and str(FechaFinal) != "False":
                diferencia = FechaFinal - FechaInicial
                self.tiempo = diferencia.total_seconds()/3600
                self.tiempo_realizado = self.tiempo * self.factor
                if self.tiempo_manual != 0:
                    self.tiempo_facturar = self.tiempo_manual            
                else:
                    self.tiempo_facturar = self.tiempo_realizado
        
    
    #Cambios en campos

    @api.onchange('factor')
    def _on_change_factor(self):        
        self.recalcular() 

    @api.onchange('tiempo_manual')
    def _on_change_tiempo_manual(self):        
        self.recalcular() 


    def check_int(self,s):
        try: 
            int(s)
        except ValueError:
            return False
        else:
            return True
        
    @api.onchange('ticket')
    def _on_change_ticket(self):
        if self.check_int(self.ticket):
            resultado = self.env['helpdesk.ticket'].search_count([('id','=',int(self.ticket))])       
            if resultado > 0:
                casos = self.env['helpdesk.ticket'].search([('id','=',int(self.ticket))])
                for caso in casos:
                    self.case_id = caso.id
                    self.partner_id = caso.partner_id
                    if caso.team_id.use_helpdesk_timesheet == True:                        
                        self.project_id = caso.team_id.project_id
            else:
                self.case_id = ""
        
        
    
    #Crear registro en ticket
    
    def imputar(self):
        resultado = self.env['account.analytic.line'].search_count([('id','=',self.account_analytic_line_id.id)]) 
        if resultado == 0:
            resultado = self.env['helpdesk.ticket'].search_count([('id','=',self.case_id.id)])       
            if resultado > 0:  
                timesheet = self.env['account.analytic.line'].create(
                    {                       
                            'date':self.fecha_final,
                            'helpdesk_ticket_id': self.case_id.id,
                            'user_id': self.user_id.id,
                            'project_id': self.project_id.id,
                            'unit_amount': self.tiempo_facturar,
                            'amount':0.00,
                            'name':self.descripcion,
                    })
                self.state = '3'
                self.account_analytic_line_id = timesheet.id
            else:
                resultado = self.env['project.task'].search_count(['&',('id','=',self.task_id.id),('project_id','=',self.project_id.id)])  
                if resultado > 0:               
                    timesheet = self.env['account.analytic.line'].create(
                        {                       
                                'date':self.fecha_final,                                
                                'user_id': self.user_id.id,
                                'project_id': self.project_id.id,
                                'task_id':self.task_id.id,
                                'unit_amount': self.tiempo_facturar,
                                'amount':0.00,
                                'name':self.descripcion,
                        })
                    self.state = '3'
                    self.account_analytic_line_id = timesheet.id
        else:
            raise ValidationError("Ya esta imputado")
            
    def unir_imputaciones(self):
        for record in self: 
            FechaInicio = record.fecha_inicio
            FechaFin = record.fecha_fin
            TiempoUtilizado = TiempoUtilizado + record.tiempo_utilizado
            
            Descripcion = Descripcion + " " +  record.descripcion
            raise ValidationError (Descripcion)
        
    