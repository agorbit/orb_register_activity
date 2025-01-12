# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class Actividades (models.Model):
    _name = 'actividades'
    _description='Actividades'

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
        ('3', 'Finalizado'),
        ('4', 'Externo')
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

    @api.onchange('factor','tiempo_manual')
    def _on_change_factor(self):        
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
                    self.project_id = caso.team_id.project_id
            else:
                self.case_id = ""
        
        