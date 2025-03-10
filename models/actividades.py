# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime,date
from odoo.exceptions import ValidationError,UserError


class Actividades (models.Model):
    _name = 'actividades'
    _description='Actividades'
    _inherit = 'mail.thread'

    name = fields.Char('name')
    company_id = fields.Many2one('res.company',string='Company', store=True, readonly=True,default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned to', store=True, readonly=False,default=lambda self: self.env.user and self.env.user.id or False )
    ticket = fields.Char('ticket')
    partner_id = fields.Many2one('res.partner', string='partner')
    partner_parent_id = fields.Many2one('res.partner', string='Cliente Padre')
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
    dias_vencido = fields.Float(compute='_compute_dias_vencido', string='Días vencido', store="True")
    
    @api.depends('fecha_vencimiento')
    def _compute_dias_vencido(self):        
        if self.fecha_vencimiento != False:
            FechaAhora = date.today()
            FechaFinal = self.fecha_vencimiento        
            diferencia = FechaAhora -  FechaFinal
            self.dias_vencido = diferencia.total_seconds()/86400
        else:
            raise UserError("No se ha establecido fecha de vencimiento")

    
    #Botones
    def borrador(self):
        self.state = '0' 

    def enprogreso(self):
        if self.case_id.id == False and self.project_id.id == False:
            raise ValidationError("Caso o proyecto deben estar rellenados")
        else:
            if self.case_id.id == False and self.project_id.id != False and self.task_id.id == False:
                raise ValidationError("Si es una imputación de proyecto, proyecto y tarea debes estar rellenados")
            else:                
                self.state = '1' 
        

    def finalizar(self):
        if self.case_id.id == False and self.project_id.id == False:
            raise ValidationError("Caso o proyecto deben estar rellenados")
        else:
            if self.case_id.id == False and self.project_id.id != False and self.task_id.id == False:
                raise ValidationError("Si es una imputación de proyecto, proyecto y tarea debes estar rellenados")
            else:                
                self.state = '3' 
                
    def imputado(self):
        if self.case_id.id == False and self.project_id.id == False:
            raise ValidationError("Caso o proyecto deben estar rellenados")
        else:
            if self.case_id.id == False and self.project_id.id != False and self.task_id.id == False:
                raise ValidationError("Si es una imputación de proyecto, proyecto y tarea debes estar rellenados")
            else:
                self.state = '3'
                  
    def externo(self):
        self.state = '4'
        
    
    #Cambios en campos
    
    @api.onchange('partner_id')
    def _on_change_partner(self):        
        if self.partner_id.parent_id.id != False:
            self.partner_parent_id = self.partner_id.parent_id.id
        else:
            self.partner_parent_id = self.partner_id.id

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
                    self.partner_id = caso.partner_id.id
                    if caso.partner_id.parent_id.id != False:
                        self.partner_parent_id = caso.partner_id.parent_id.id  
                    if caso.team_id.use_helpdesk_timesheet == True:                        
                        self.project_id = caso.team_id.project_id
                    else:
                        raise UserError("No esta activado timesheet en el equipo de ticket")
            else:
                self.case_id = ""
        
        