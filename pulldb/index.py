# Copyright 2013 Russell Heilling
from pulldb import base

class MainPage(base.BaseHandler):
  def get(self):
    template_values = self.base_template_values()
    template = self.templates.get_template('index.html')
    self.response.write(template.render(template_values))

app = base.create_app([
    ('/', MainPage),
])
