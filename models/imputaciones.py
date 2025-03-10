# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError,UserError


class Imputaciones (models.Model):
    _name = 'imputaciones'
    _description='Imputaciones de actividades'
    _inherit = 'mail.thread'
    

    name = fields.Char('name')
    company_id = fields.Many2one('res.company',string='Company', store=True, readonly=True,default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned to', store=True, readonly=False,default=lambda self: self.env.user and self.env.user.id or False )
    ticket = fields.Char('ticket')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    partner_parent_id = fields.Many2one('res.partner', string='Cliente Padre')
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
    agrupacion = fields.Boolean('agrupacion',default=False)
    agrupacion_lines_ids = fields.One2many('imputaciones', 'imputacion_id', string='Lineas agrupacion')
    imputacion_id = fields.Many2one('imputaciones', string='Imputacion')
    where = fields.Char(compute='_compute_where', string='where')
    
    
    
    @api.depends('partner_id','project_id')
    def _compute_where(self):
        if self.partner_id.id != False:
            where = "('partner_id','=','" + str(self.partner_id.id) + ")"
            if self.project_id.id != False:
                where = "'&'," + where + "('project_id','=','" + str(self.project_id.id) + ")"                
        
        where = "[" + where + "]"
        
    #eMetodos de crear,elimna y actualizar
    def unlink(self):
        for record in self:
            if record.imputacion_id.id != False:
               raise ValidationError("No se puede elimina porque pertenee a una agrupación") 
            if record.agrupacion == True:
                resultado = self.env['imputaciones'].search([('imputacion_id','=',record.id)])
                for record in resultado:                    
                    record.imputacion_id = ''
                    record.state = '2'
        imputaciones = super(Imputaciones,self).unlink()
        return imputaciones
    
    def enprogreso(self):
        if self.imputacion_id.id != False:
            raise ValidationError("No se puede modificar porque pertenee a una agrupación") 
        else:
            state = '1'
            self.fecha_inicio = datetime.today()

    def finalizar(self):
        if self.case_id.id == False and self.project_id.id == False:
            raise ValidationError("Caso o proyecto deben estar rellenados")
        else:
            if self.case_id.id == False and self.project_id.id != False and self.task_id.id == False:
                raise ValidationError("Si es una imputación de proyecto, proyecto y tarea debes estar rellenados")
            else:                
                self.state = '2'
                if self.agrupacion == False: #A los agrupados no recalcula
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
        if self.state in ('1','2'):
            if str(self.fecha_final) == "" :
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

    @api.onchange('fecha_final')
    def _on_change_fecha_final(self):        
        self.recalcular() 
        
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
                        raise ValidationError("No esta activado timesheet en el equipo de ticket")
            else:
                self.case_id = ""
        
    @api.onchange('case_id')
    def _on_change_case_id(self):  
        if self.case_id.id != False:
            self.partner_id = self.case_id.partner_id.id 
            if self.partner_id.parent_id.id != False:
                self.partner_parent_id = self.partner_id.parent_id.id 
            else:                
                self.partner_parent_id = self.case_id.partner_id.id                
            if self.case_id.team_id.use_helpdesk_timesheet == True:                        
                self.project_id = self.case_id.team_id.project_id.id 
    
    #Crear registro en ticket
    
    def imputar(self):
        for record in self:
            if record.state == '2':
                resultado = self.env['account.analytic.line'].search_count([('id','=',record.account_analytic_line_id.id)]) 
                if resultado == 0:
                    resultado = self.env['helpdesk.ticket'].search_count([('id','=',record.case_id.id)])       
                    if resultado > 0:  
                        timesheet = self.env['account.analytic.line'].create(
                            {                       
                                    'date':record.fecha_final,
                                    'helpdesk_ticket_id': record.case_id.id,
                                    'user_id': record.user_id.id,
                                    'project_id': record.project_id.id,
                                    'unit_amount': record.tiempo_facturar,
                                    'amount':0.00,
                                    'name':record.descripcion,
                            })
                        record.state = '3'
                        record.account_analytic_line_id = timesheet.id
                    else:
                        resultado = self.env['project.task'].search_count(['&',('id','=',record.task_id.id),('project_id','=',record.project_id.id)])  
                        if resultado > 0:               
                            timesheet = self.env['account.analytic.line'].create(
                                {                       
                                        'date':record.fecha_final,                                
                                        'user_id': record.user_id.id,
                                        'project_id': record.project_id.id,
                                        'task_id':record.task_id.id,
                                        'unit_amount': record.tiempo_facturar,
                                        'amount':0.00,
                                        'name':record.descripcion,
                                })
                            record.state = '3'
                            record.account_analytic_line_id = timesheet.id
                else:
                    raise ValidationError("Ya esta imputado")
            else:
                    raise ValidationError("No se puede imputar en estado")
            
    def unir_imputaciones(self):
        
        CamposUnicos = self.mapped('partner_id')
        if len(set(CamposUnicos)) == 1:        
            pass
        else:
            raise ValidationError("Distintos clientes")

        CamposUnicos = self.mapped('case_id')
        if len(set(CamposUnicos)) == 1 or len(set(CamposUnicos)) == 0:       
            pass
        else:
            raise ValidationError("Distintos tickets")

        CamposUnicos = self.mapped('project_id')
        if len(set(CamposUnicos)) == 1:        
            pass
        else:
            raise ValidationError("Distintos proyectos")

        
        CamposUnicos = self.mapped('task_id')        
        if len(set(CamposUnicos)) == 1 or len(set(CamposUnicos)) == 0:        
            pass
        else:
            raise ValidationError("Distintas tareas")

        CamposUnicos = self.mapped('fecha_final')
        CamposUnicos = [dt.date() for dt in CamposUnicos]        
        if len(set(CamposUnicos)) == 1:        
            pass
        else:
            raise ValidationError("Distintas fechas")
        
        TiempoRealizado = 0
        TiempoFacturable = 0
        TiempoManual = 0
        Descripcion = ""
        Resumen = ""
        for record in self: 
            FechaInicio = record.fecha_inicio
            FechaFin = record.fecha_final            
            TiempoManual = TiempoManual + record.tiempo_facturar
            if str(record.name) == 'False':
                Resumen = Resumen + ''
            else:
                Resumen = Resumen + ' ' + record.name
            if str(record.descripcion) == 'False':
                Descripcion = Descripcion + ''
            else:
                Descripcion = Descripcion + ' ' + record.descripcion
            State = record.state
            Tarea = record.task_id.id
        
        NewCase = self.env['imputaciones'].create(
            {
                'partner_id':record.partner_id.id,
                'partner_parent_id':record.partner_parent_id.id,
                'project_id':record.project_id.id,
                'case_id': record.case_id.id,
                'task_id': Tarea,
                'fecha_inicio':FechaInicio,
                'fecha_final':FechaFin,
                'tiempo_manual': TiempoManual,                
                'tiempo_facturar':TiempoManual,
                'name':Resumen,
                'descripcion':Descripcion,
                'agrupacion': True,
                'state': State
            })
        agrupacion_nueva = NewCase.id     
        
        for record in self:            
            self.imputacion_id = NewCase.id
            self.state = '3'
        
    