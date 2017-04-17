
# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, exceptions

class Project(models.Model):

    _name = 'agili.project'

    name = fields.Char(string="Nombre del Proyecto", required=True)

    description = fields.Text(string="Descripción")

    start_date = fields.Date(string="Fecha de inicio", required=True)

    end_date = fields.Date(string="Fecha de Fin", required=True)

    hour_man = fields.Integer(string="Horas hombres")

    responsible_ids = fields.Many2many('res.users', 
                                        string="Responsables")


    porcen_project = fields.Float(string="Avance del proyecto",
                                  compute='_porcent_project', 
                                  store=True)

    activity_ids = fields.One2many(
        'agili.activity', 'ac_project_id', string="Actividades")

    activities_count = fields.Integer(string="Numero de actividades", 
                                    compute='_get_activities_count', 
                                    store=True)

    deliverable_ids = fields.One2many(
        'agili.deliverable', 'de_project_id', string="Entregables")


    _sql_constraints = [
        ('name_description_check',
        'CHECK(name != description)',
        "El nombre del proyecto no puede ser la descripción."),

        ('name_unique',
        'UNIQUE(name)',
        "El nombre del proyecto es unico"),

        ('hour_valid',
        'CHECK(hour_man <= 0)',
        "Las horas hombre tienen que ser mayor a 0"),
    ]

    state = fields.Selection([
        ('process', "En proceso"),
        ('stopped', "Detenido"),
        ('done', "Terminado"),
    ], string="Estado", default='process')

    @api.multi
    def action_process(self):
        self.state = 'process'

    @api.multi
    def action_stopped(self):
        self.state = 'stopped'

    @api.multi
    def action_done(self):
        self.state = 'done'

    #Función para calcular cuantas acitvidades hay en proyecto
    @api.depends('activity_ids')
    def _get_activities_count(self):
        for r in self:
            r.activities_count = len(r.activity_ids)
            print r.activities_count

    #Funcion para calcular el porcentaje ejecutado de un proyecto
    @api.depends('activity_ids')
    def _porcent_project(self):
        for r in self:
            if not r.activity_ids:

                r.porcen_project = 0.0
            
            else:

                num_done = 0

                for act in r.activity_ids:
                    
                    if act.ac_state == 'done':

                        num_done +=1

                r.porcen_project = 100 * num_done / len(r.activity_ids)

    @api.model
    def print_report(self):

        context = self.env.context
    
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'agili.report_general',
            'context': context,
        }

class Activity(models.Model):

    _name = 'agili.activity'

    name = fields.Char(string="Nombre de Actividad", required=True)
    
    ac_start_date = fields.Date(string="Fecha de inicio", required=True)

    ac_end_date = fields.Date(string="Fecha de Fin", required=True)
   
    objetive = fields.Char(string="Objetivo", required=True)
    
    description = fields.Text(string="Descripción")

    result = fields.Text(string="Resultado")

    ac_hour_man = fields.Integer(string="Horas hombres")

    ac_responsible_id = fields.Many2one('res.users',
    ondelete='set null', string="Responsable", index=True)

    ac_project_id = fields.Many2one('agili.project',
        ondelete='cascade', string="Proyecto", required=True)

    _sql_constraints = [
        ('name_description_check',
        'CHECK(name != description)',
        "El nombre de la actividad no puede ser la descripción."),

        ('name_unique',
        'UNIQUE(name)',
        "El nombre de la actividad es unica"),

        ('hour_valid',
        'CHECK(ac_hour_man <= 0)',
        "Las horas hombre tienen que ser mayor a 0"),
        
    ]

    ac_state = fields.Selection([
        ('process', "En proceso"),
        ('stopped', "Detenida"),
        ('done', "Terminada"),
    ], string="Estado", default='process')

    @api.multi
    def action_process(self):
        self.ac_state = 'process'

    @api.multi
    def action_stopped(self):
        self.ac_state = 'stopped'

    @api.multi
    def action_done(self):
        self.ac_state = 'done'


class Deliverable(models.Model):
    
    _name = 'agili.deliverable'

    name = fields.Char(string="Nombre", 
                       required=True)

    deliverable = fields.Binary(string="Entregable", 
                                attachment=True,
                                required=True)

    de_project_id = fields.Many2one('agili.project',
                                ondelete='cascade', 
                                string="Proyecto", 
                                required=True)

class report_project_general(models.AbstractModel):
    _name = 'report.agili.report_general'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('agili.report_general')
        projects = self.env['agili.project'].search([('hour_man','>=', 0)])
        
        docargs = {
            'doc_model': report.model,
            'data': self._get_data_general(),
        }

        return report_obj.render('agili.report_general', docargs)

    def _get_data_general(self):

        data = {}

        data['pro_done'] = 0
        data['pro_process'] = 0
        data['pro_stopped'] = 0

        data['hour_done'] = 0
        data['hour_process'] = 0
        data['hour_stopped'] = 0

        data['pro_porcen'] = 0
        data['hour_total'] = 0
        data['hour_porcen'] = 0

        projects = self.env['agili.project'].search([('hour_man','>=', 0)])

        data['len_project'] = len(projects)

        for project in projects:

            if project.state == 'done':

                data['pro_done'] += 1
                data['hour_done'] += project.hour_man

            if project.state == 'process':

                data['pro_process'] += 1
                data['hour_process'] +=  project.hour_man


            if project.state == 'stopped':

                data['pro_stopped'] += 1
                data['hour_stopped'] +=  project.hour_man


        data['pro_porcen'] = data['pro_done'] * 100 / data['len_project'] 

        data['hour_total'] = data['hour_done'] + data['hour_process'] + data['hour_stopped']
        data['hour_porcen'] = data['hour_done'] * 100 / data['hour_total'] 

        return data
